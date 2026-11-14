"""Endpoints que usa la API Java (regla de arquitectura, doc 29):
Python descarga los datos NASA y CALCULA; Java lee y graba la base de datos y responde a la app.

- POST /calcular            → datos NASA del punto + recomendación completa (forma de la app) + forma del contrato
- POST /indicadores-punto   → datos NASA + los 4 indicadores (para el mapa por valle)
- POST /validacion          → máquina del tiempo (serie mensual, alerta, semanas de anticipación)
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import nasa_cliente as nasa
from .crops import DatosInvalidos
from .indicators import calcular_indicadores
from .que_hacer import construir_que_hacer
from .rotations import rotaciones_para
from .schemas import Cultivo, IndicadoresRequest, RecomendacionResponse, RotacionCandidata

router = APIRouter(tags=["allpashift (Java → Python)"])
MES_NOMBRE = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ------------------------------------------------------------------ modelos de entrada
class CultivoCatalogo(Cultivo):
    """Fila del catálogo que manda Java (agro.v_cultivos_contrato + agro.cultivos)."""
    cicloDias: int | None = None
    toleraSequia: bool = False
    toleraInundacion: bool = False


class Permanente(BaseModel):
    nombre: str
    calendario: str = Field(min_length=12, max_length=12, description="12 letras ene..dic: S C F K D")
    fases: dict[str, str] = Field(default_factory=dict)
    acciones: list[dict[str, Any]] = Field(default_factory=list)


class CalcularRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    fecha: date | None = None
    tipoCultivo: Literal["temporal", "permanente"] = "temporal"
    mesSiembra: str | None = Field(default=None, description="AAAA-MM")
    cultivos: list[CultivoCatalogo] = Field(default_factory=list)
    rotaciones: list[RotacionCandidata] | None = None
    rotacionActualId: int | None = None
    top: int = 3
    permanente: Permanente | None = None


class PuntoRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Evento(BaseModel):
    nombre: str
    inicio: date
    fin: date | None = None


class ValidacionRequest(PuntoRequest):
    anio: int = Field(ge=1981, le=2100)
    eventos: list[Evento] = Field(default_factory=list)


# ------------------------------------------------------------------ datos NASA → entrada del contrato
def datos_nasa(lat: float, lon: float) -> dict[str, Any]:
    try:
        clim = nasa.climatologia(lat, lon)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"NASA POWER no respondió: {e}") from e
    return {"climatologia": clim, "reciente": nasa.reciente(lat, lon), "sstAnomalia": nasa.sst_anomalia(lat, lon), "fuente": "NASA POWER"}


def entrada_contrato(lat: float, lon: float, d: dict[str, Any]) -> IndicadoresRequest:
    m = date.today().month - 1
    c, r, sst = d["climatologia"], d["reciente"], d["sstAnomalia"]
    hist = {"lluviaMm": round(c["PRECTOTCORR"][m], 2), "humedadSuelo": round(c["GWETTOP"][m], 3),
            "tempMaxC": round(c["T2M_MAX"][m], 1), "tempMinC": round(c["T2M_MIN"][m], 1)}
    act = dict(hist)
    if r:
        act = {"lluviaMm": round(r["lluviaMmDia"], 2), "humedadSuelo": round(r["humedadSup"], 3),
               "tempMaxC": round(r["tMax"], 1), "tempMinC": round(r["tMin"], 1)}
    act["sstAnomaliaC"] = round(sst, 2) if sst is not None else 0.0
    meta = {"lluvia": {"fuente": "NASA POWER", "unidad": "mm/día"}, "humedadSuelo": {"fuente": "NASA POWER", "unidad": "fracción 0-1"},
            "calor": {"fuente": "NASA POWER", "unidad": "°C"}, "elNino": {"fuente": "MUR SST" if sst is not None else "sin dato", "unidad": "°C anomalía"}}
    return IndicadoresRequest(lat=lat, lon=lon, actual=act, historico=hist, meta=meta)


def indicadores_app(ind: Any, hay_sst: bool) -> dict[str, Any]:
    """Indicadores con el campo opcional 'detalle'; sin MUR SST no se muestra El Niño."""
    out = {}
    for k, v in ind.model_dump().items():
        if k == "elNino" and not hay_sst:
            continue
        v["detalle"] = _detalle(k, v["valor"], v["normal"])
        out[k] = v
    return out


def _detalle(k: str, valor: float, normal: float) -> str:
    if k == "lluvia":
        if normal < 3:
            return f"Lluvia de {valor:.1f} mm/día frente a {normal:.1f} mm/día normales ({valor * 30:.0f} mm en 30 días)"
        return f"Lluvia {abs(valor / normal - 1) * 100:.0f} % {'por debajo' if valor < normal else 'por encima'} de lo normal"
    if k == "humedadSuelo":
        return f"Humedad del suelo {abs(valor / max(normal, 0.01) - 1) * 100:.0f} % {'por debajo' if valor < normal else 'por encima'} de lo normal"
    if k == "calor":
        return f"Máxima de {valor:.1f} °C frente a {normal:.1f} °C normales"
    return f"Mar {abs(valor):.1f} °C {'más caliente' if valor >= 0 else 'más frío'} de lo normal frente a la costa"


def _nivel(ind: dict[str, Any], k: str) -> str | None:
    return ind.get(k, {}).get("nivel")


# ------------------------------------------------------------------ perspectiva de la campaña
def _sumar_meses(ym: tuple[int, int], k: int) -> tuple[int, int]:
    a, m = ym
    t = a * 12 + (m - 1) + k
    return t // 12, t % 12 + 1


def ciclo(c1: CultivoCatalogo, c2: CultivoCatalogo, siembra: tuple[int, int], clim: dict, ind: dict) -> dict[str, Any]:
    m1 = max(2, math.ceil((c1.cicloDias or 120) / 30))
    m2 = max(2, math.ceil((c2.cicloDias or 120) / 30))
    dur = min(m1 + max(1, m2 // 2), 9)
    lluvia, tmax = clim["PRECTOTCORR"], clim["T2M_MAX"]
    maximo = max(v * 30 for v in lluvia)
    nino = "alto" in (_nivel(ind, "elNino"), _nivel(ind, "lluvia"))
    meses, peor, peor_n = [], None, 0
    for k in range(dur):
        a, m = _sumar_meses(siembra, k)
        c = c1 if k < m1 else c2
        riesgo, motivo, fuente = "bajo", f"Condiciones normales para {c.nombre.lower()}", "NASA POWER"
        lm = lluvia[m - 1] * 30
        if k == 0 and _nivel(ind, "humedadSuelo") == "alto" and not c.toleraSequia:
            riesgo, motivo = "alto", "Suelo seco al sembrar"
        elif k == 0 and _nivel(ind, "lluvia") == "alto" and not c.toleraInundacion:
            riesgo, motivo = "alto", "Lluvia actual muy por encima de lo normal: riesgo de encharcamiento"
        elif lm >= 0.6 * maximo and lm >= 25 and not c.toleraInundacion:
            riesgo = "alto" if nino else "medio"
            motivo = "Temporada de lluvias, exceso de humedad" + (" y señal de El Niño" if nino else "")
            fuente = "NASA POWER + MUR SST" if nino else fuente
        elif tmax[m - 1] >= c.tempMaxC:
            riesgo, motivo = "medio", f"Calor: la máxima normal es {tmax[m - 1]:.1f} °C"
        mes = f"{a}-{m:02d}"
        meses.append({"mes": mes, "riesgo": riesgo, "motivo": motivo, "fuente": fuente})
        n = {"alto": 2, "medio": 1}.get(riesgo, 0)
        if n > peor_n:
            peor_n, peor = n, mes
    a2, m2_ = _sumar_meses(siembra, dur - 1)
    out = {"siembra": f"{siembra[0]}-{siembra[1]:02d}", "cosecha": f"{a2}-{m2_:02d}", "duracionMeses": dur, "meses": meses}
    if peor:
        out["mesMasRiesgoso"] = peor
    return out


def plan_permanente(p: Permanente, clim: dict, ind: dict, hoy: date) -> dict[str, Any]:
    lluvia = clim["PRECTOTCORR"]
    maximo = max(v * 30 for v in lluvia)
    nino = "alto" in (_nivel(ind, "elNino"), _nivel(ind, "lluvia"))
    meses = []
    for k in range(12):
        a, m = _sumar_meses((hoy.year, hoy.month), k)
        letra = p.calendario[m - 1]
        etapa = p.fases.get(letra, "crecimiento").lower()
        riesgo, motivo = "bajo", "Condiciones normales"
        lm = lluvia[m - 1] * 30
        if lm >= 0.6 * maximo and lm >= 25:
            riesgo = "alto" if nino else "medio"
            motivo = "Temporada de lluvias" + {"K": " durante la cosecha", "F": " durante la floración"}.get(letra, "") + (" y señal de El Niño" if nino else "")
        meses.append({"mes": f"{a}-{m:02d}", "riesgo": riesgo, "motivo": motivo, "fuente": "NASA POWER + MUR SST" if nino else "NASA POWER", "etapa": etapa})
    acciones = [{"etapa": p.fases.get(x.get("fase", ""), x.get("fase", "")).lower(), "accion": x.get("descripcion", ""),
                 "motivo": x.get("alerta") or "", "fuente": "NASA POWER"} for x in p.acciones]
    return {"cultivo": p.nombre, "etapaActual": meses[0]["etapa"], "meses": meses, "acciones": acciones}


def que_hacer_permanente(p: Permanente, plan: dict, ind: dict) -> dict[str, Any]:
    etapa, nombre = plan["etapaActual"], p.nombre.lower()
    if "alto" in (_nivel(ind, "lluvia"), _nivel(ind, "elNino")):
        k = "elNino" if _nivel(ind, "elNino") == "alto" else "lluvia"
        return {"tipo": "preparar drenaje", "accion": f"Prepara drenajes y protege tu {nombre} ({etapa})",
                "motivo": ind[k]["detalle"], "fuente": ind[k]["fuente"]}
    if _nivel(ind, "humedadSuelo") == "alto":
        return {"tipo": "regar", "accion": f"Refuerza el riego de tu {nombre}: el suelo está seco",
                "motivo": ind["humedadSuelo"]["detalle"], "fuente": ind["humedadSuelo"]["fuente"]}
    texto = next((a["accion"] for a in plan["acciones"] if a["etapa"] == etapa), "Mantén el riego y la sanidad del cultivo")
    return {"tipo": "regar", "accion": texto, "motivo": f"Tu {nombre} está en {etapa} y el clima está dentro de lo normal", "fuente": "NASA POWER"}


def tipo_accion(accion: str) -> str:
    a = (accion or "").lower()
    if "drena" in a:
        return "preparar drenaje"
    if "esper" in a or "no siembres" in a or "todavía no" in a:
        return "esperar"
    if "proteg" in a:
        return "proteger"
    if "reg" in a:
        return "regar"
    return "sembrar"


def _agua_nivel(a: str) -> str:
    return {"baja": "bajo", "alta": "alto"}.get(a, "medio")


# ------------------------------------------------------------------ endpoints
@router.post("/calcular", summary="Descarga datos NASA del punto y calcula la recomendación completa")
def calcular(req: CalcularRequest) -> dict[str, Any]:
    hoy = req.fecha or date.today()
    d = datos_nasa(req.lat, req.lon)
    entrada = entrada_contrato(req.lat, req.lon, d)
    ind_obj = calcular_indicadores(entrada)
    ind = indicadores_app(ind_obj, d["sstAnomalia"] is not None)
    contrato = None
    reco: dict[str, Any] = {"lat": req.lat, "lon": req.lon, "fecha": hoy.isoformat(), "indicadores": ind}

    if req.tipoCultivo == "permanente":
        if not req.permanente:
            raise HTTPException(status_code=422, detail="Falta 'permanente' (nombre y calendario del cultivo)")
        plan = plan_permanente(req.permanente, d["climatologia"], ind, hoy)
        reco.update({"rotaciones": [], "plan": plan, "queHacer": que_hacer_permanente(req.permanente, plan, ind)})
    else:
        if not req.cultivos:
            raise HTTPException(status_code=422, detail="Falta el catálogo de cultivos")
        try:
            elegidas, todas = rotaciones_para(ind_obj, list(req.cultivos), req.rotaciones, hoy, req.top, req.rotacionActualId, False)
        except DatosInvalidos as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        qh = construir_que_hacer(ind_obj, elegidas, todas)
        contrato = RecomendacionResponse(lat=req.lat, lon=req.lon, fecha=hoy, indicadores=ind_obj,
                                         rotaciones=[e.resultado for e in elegidas], queHacer=qh)
        extras = {c.id: c for c in req.cultivos}
        siembra = (int(req.mesSiembra[:4]), int(req.mesSiembra[5:7])) if req.mesSiembra else (hoy.year, hoy.month)
        rots = []
        for e in elegidas:
            r = e.resultado.model_dump(exclude_none=True)
            c1, c2 = extras.get(e.cultivo1.id), extras.get(e.cultivo2.id)
            if c1 and c2:
                r["usoAgua"] = _agua_nivel(max(c1.aguaNecesaria, c2.aguaNecesaria, key=["baja", "media", "alta"].index))
                r["ciclo"] = ciclo(c1, c2, siembra, d["climatologia"], ind)
            rots.append(r)
        reco.update({"rotaciones": rots, "queHacer": {**qh.model_dump(), "tipo": tipo_accion(qh.accion)}})

    return {"datosNasa": _datos_para_guardar(req.lat, req.lon, d), "recomendacion": reco,
            "contrato": contrato.model_dump(mode="json") if contrato else None}


@router.post("/indicadores-punto", summary="Datos NASA + los 4 indicadores de un punto (mapa)")
def indicadores_punto(req: PuntoRequest) -> dict[str, Any]:
    d = datos_nasa(req.lat, req.lon)
    ind = indicadores_app(calcular_indicadores(entrada_contrato(req.lat, req.lon, d)), d["sstAnomalia"] is not None)
    orden = {"alto": 2, "medio": 1, "bajo": 0}
    nivel = max((v["nivel"] for v in ind.values()), key=lambda n: orden[n], default=None)
    return {"datosNasa": _datos_para_guardar(req.lat, req.lon, d), "indicadores": ind, "nivel": nivel}


@router.post("/validacion", summary="Máquina del tiempo: qué habría dicho AllpaShift ese año")
def validacion(req: ValidacionRequest) -> dict[str, Any]:
    try:
        serie = nasa.mensual(req.lat, req.lon, req.anio)
        clim = nasa.climatologia(req.lat, req.lon)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"NASA POWER no respondió: {e}") from e
    dias = [31, 29 if req.anio % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    valores = [None if v is None else round(v * dias[m], 1) for m, v in enumerate(serie["PRECTOTCORR"])]
    normal = [round(clim["PRECTOTCORR"][m] * dias[m], 1) for m in range(12)]
    hum = [None if v is None else round(v, 2) for v in serie["GWETROOT"]]
    hum_n = [round(v, 2) for v in clim["GWETROOT"]]
    con_dato = [m for m in range(12) if valores[m] is not None]
    mmax = max(con_dato, key=lambda m: valores[m]) if con_dato else None
    alerta = None
    for m in con_dato:
        v, n = valores[m], normal[m]
        if v > max(3 * n, 30):
            fecha = f"{req.anio}-{m + 1:02d}-15"
            motivo = f"En {MES_NOMBRE[m]} llovieron {v:.0f} mm frente a {n:.0f} mm normales ({v / max(n, 1):.1f} veces)"
            alerta = {"fecha": fecha, "accion": "Preparar drenaje y no sembrar en zonas bajas", "motivo": motivo, "indicador": "lluvia",
                      "nivel": "alto", "valor": v, "fuente": "NASA POWER", "alertaDrenaje": {"fecha": fecha, "valor": v, "fuente": "NASA POWER"},
                      "nota": "Alerta calculada con la lluvia mensual de NASA POWER"}
            break
    semanas = None
    if alerta and mmax is not None:
        semanas = max(0, (date(req.anio, mmax + 1, 15) - date.fromisoformat(alerta["fecha"])).days // 7)
    evento = next(({"nombre": e.nombre, "inicio": e.inicio.strftime("%Y-%m"), "fin": (e.fin or date.today()).strftime("%Y-%m")}
                   for e in req.eventos if e.inicio.year <= req.anio <= (e.fin or date.today()).year), None)
    realidad = {
        2017: {"resumen": "El Niño Costero de 2017 causó inundaciones en Piura (desborde del río Piura el 27 de marzo) y miles de hectáreas perdidas.", "fuente": "INDECI / SENASA"},
        1998: {"resumen": "El Niño 1997-98 fue extraordinario: lluvias de hasta 16 mm/día en enero en Piura.", "fuente": "ENFEN"},
        2023: {"resumen": "El Niño costero de 2023 trajo calor y lluvias que afectaron mango y uva.", "fuente": "ENFEN"},
    }.get(req.anio)
    previa = ({"tipo": "preparar drenaje", "accion": "Preparar drenaje y adelantar la cosecha", "motivo": alerta["motivo"], "fuente": "NASA POWER"}
              if alerta else {"tipo": "sembrar", "accion": "Sembrar con normalidad", "motivo": "La lluvia del año estuvo dentro de lo normal", "fuente": "NASA POWER"})
    mes_max = f"{req.anio}-{mmax + 1:02d}" if mmax is not None else None
    return {
        "anio": req.anio, "lat": req.lat, "lon": req.lon, "evento": evento,
        "series": {"lluvia": {"unidad": "mm/mes", "fuente": "NASA POWER", "valores": valores, "normal": normal, "producto": "POWER PRECTOTCORR"},
                   "humedadSuelo": {"unidad": "fracción 0-1", "fuente": "NASA POWER", "valores": hum, "normal": hum_n, "producto": "POWER GWETROOT"}},
        "alerta": alerta, "mesLluviaMaxima": mes_max, "semanasAnticipacion": semanas, "realidad": realidad, "recomendacionPrevia": previa,
        "resumen": (f"AllpaShift habría dado la alerta el {alerta['fecha']}, {semanas} semanas antes del mes más lluvioso ({mes_max})."
                    if alerta else "Ese año la lluvia no superó el umbral de alerta."),
    }


def _datos_para_guardar(lat: float, lon: float, d: dict[str, Any]) -> list[dict[str, Any]]:
    """Filas para nasa.datos_nasa (formato del contrato: lat, lon, fecha, fuente, variable, valor). Las graba Java."""
    filas: list[dict[str, Any]] = []
    r = d["reciente"]
    if r:
        f = f"{r['ultimoDia'][:4]}-{r['ultimoDia'][4:6]}-{r['ultimoDia'][6:]}"
        for var, val in (("PRECTOTCORR:lluviaMm", r["lluviaMmDia"]), ("GWETTOP:humedadSuelo", r["humedadSup"]),
                         ("T2M_MAX:tempMaxC", r["tMax"]), ("T2M_MIN:tempMinC", r["tMin"])):
            filas.append({"lat": lat, "lon": lon, "fecha": f, "fuente": "NASA POWER", "variable": var + ":prom30d", "valor": round(val, 4)})
    if d["sstAnomalia"] is not None:
        filas.append({"lat": lat, "lon": lon, "fecha": date.today().isoformat(), "fuente": "MUR SST", "variable": "sstAnom:sstAnomaliaC", "valor": round(d["sstAnomalia"], 3), "version": "4.1"})
    return filas
