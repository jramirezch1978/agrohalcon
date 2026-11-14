"""Análisis estadístico sobre los datos de la base: tendencias (Mann-Kendall + pendiente de Sen) y el
contraste "años con Niño costero vs años normales". Todo reproducible: los años Niño se calculan del índice
Niño 1+2 de NOAA, no se escriben a mano.
"""

import pandas as pd
import pymannkendall as mk

VARIABLES_TENDENCIA = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT", "EVPTRNS"]
SENTIDOS = {"increasing": "creciente", "decreasing": "decreciente", "no trend": "sin tendencia"}


def tendencias(mensual: pd.DataFrame, anio_ini: int = 1981, anio_fin: int = 2025) -> pd.DataFrame:
    """`mensual`: columnas zona_id, variable (código), fecha (datetime), valor. Promedio anual por zona y variable,
    solo años completos (12 meses), prueba de Mann-Kendall original y pendiente de Sen por década."""
    m = mensual[mensual["variable"].isin(VARIABLES_TENDENCIA)].copy()
    m["anio"] = m["fecha"].dt.year
    anual = m.groupby(["zona_id", "variable", "anio"]).agg(valor=("valor", "mean"), meses=("valor", "size")).reset_index()
    anual = anual[(anual["meses"] == 12) & anual["anio"].between(anio_ini, anio_fin)]
    filas = []
    for (zona, var), g in anual.groupby(["zona_id", "variable"]):
        g = g.sort_values("anio")
        if len(g) < 20:
            continue
        r = mk.original_test(g["valor"].to_numpy())
        filas.append(
            {
                "zona_id": int(zona), "variable": var, "anio_ini": int(g["anio"].min()), "anio_fin": int(g["anio"].max()),
                "metodo": "Mann-Kendall + Sen", "tau": float(r.Tau), "p_valor": float(r.p),
                "pendiente_sen_por_decada": float(r.slope) * 10, "sentido": SENTIDOS[r.trend],
            }
        )  # fmt: skip
    return pd.DataFrame(filas)


def anios_nino_costero(nino: pd.DataFrame, umbral: float = 1.0) -> list[int]:
    """Años cuya anomalía media de Niño 1+2 en dic(año previo)-abr (la temporada de lluvias de la costa) es >= umbral.
    `nino`: columnas fecha (datetime), nino12_anom."""
    n = nino.set_index("fecha")["nino12_anom"].sort_index()
    años = []
    for anio in range(n.index.year.min() + 1, n.index.year.max() + 1):
        ventana = n[(n.index >= f"{anio - 1}-12-01") & (n.index <= f"{anio}-04-30")]
        if len(ventana) >= 5 and ventana.mean() >= umbral:
            años.append(anio)
    return años


def composite_nino(mensual: pd.DataFrame, años_nino: list[int], variables=("PRECTOTCORR",), meses=range(1, 7)) -> pd.DataFrame:
    """Media mensual en años Niño frente a años no Niño (1981-2025, sin el año en curso)."""
    m = mensual[mensual["variable"].isin(variables) & (mensual["fecha"].dt.year <= 2025)].copy()
    m["anio"], m["mes"] = m["fecha"].dt.year, m["fecha"].dt.month
    m["grupo"] = m["anio"].isin(años_nino).map({True: "nino", False: "normal"})
    m = m[m["mes"].isin(list(meses))]
    t = m.groupby(["zona_id", "variable", "mes", "grupo"])["valor"].agg(["mean", "size"]).unstack("grupo")
    t.columns = [f"{a}_{b}" for a, b in t.columns]
    t = t.dropna().reset_index()
    t["razon"] = t["mean_nino"] / t["mean_normal"].where(t["mean_normal"] > 0)
    return t.rename(
        columns={"mean_nino": "media_nino", "mean_normal": "media_normal", "size_nino": "n_nino", "size_normal": "n_normal"}
    )
