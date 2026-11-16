package pe.halcondorado.allpashift.api;

import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicReference;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import pe.halcondorado.allpashift.api.RecomendacionService.Respuesta;
import pe.halcondorado.allpashift.calculos.CalculosClient;
import pe.halcondorado.allpashift.calculos.NombresCultivo;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.ConsultasRepository;

/**
 * API que consume la app (web y móvil). Regla (doc 29): Java lee primero PostgreSQL; si no hay dato fresco,
 * el servicio de cálculos (Python) descarga de la NASA y calcula, y Java graba el resultado. Java no llama a la NASA.
 * Si Python no responde: último dato guardado con header X-Desde-Cache: true; si no hay, 503 (ver ErroresApi).
 */
@RestController
@RequestMapping("/api")
public class ApiController {

    private static final Logger log = LoggerFactory.getLogger(ApiController.class);

    private final RecomendacionService reco;
    private final CatalogoRepository catalogo;
    private final ConsultasRepository consultas;
    private final CalculosClient calculos;
    private final JsonUtil json;

    public ApiController(RecomendacionService reco, CatalogoRepository catalogo, ConsultasRepository consultas,
                         CalculosClient calculos, JsonUtil json) {
        this.reco = reco;
        this.catalogo = catalogo;
        this.consultas = consultas;
        this.calculos = calculos;
        this.json = json;
    }

    @GetMapping("/recomendacion")
    public ResponseEntity<Map<String, Object>> recomendacion(@RequestParam double lat, @RequestParam double lon,
                                                             @RequestParam(defaultValue = "es") String lang,
                                                             @RequestParam(required = false) String tipoCultivo,
                                                             @RequestParam(required = false) String mesSiembra,
                                                             @RequestParam(required = false) String cultivo,
                                                             @RequestParam(required = false) String prioridad,
                                                             @RequestParam(required = false) String tipoSuelo,
                                                             @RequestParam(required = false) String salinidad,
                                                             @RequestParam(required = false) String fuenteSuelo,
                                                             @RequestParam(required = false) String aguaDisponible,
                                                             @RequestParam(required = false) String escenario,
                                                             @RequestParam(required = false) Double ninoHipotetico) {
        ErroresApi.validarCoordenadas(lat, lon);
        ErroresApi.validarLang(lang);
        var perfil = PerfilAgricultor.de(prioridad, tipoSuelo, salinidad, fuenteSuelo, aguaDisponible, escenario, ninoHipotetico);
        return responder(reco.recomendacion(lat, lon, lang, tipoCultivo, mesSiembra, cultivo, perfil));
    }

    /** Tipo de suelo PROPUESTO para la parcela (SoilGrids, ISRIC; no es dato NASA). Python lo guarda en caché 90 días. */
    @GetMapping("/suelo")
    public Map<String, Object> suelo(@RequestParam double lat, @RequestParam double lon) {
        ErroresApi.validarCoordenadas(lat, lon);
        return calculos.suelo(lat, lon);
    }

    /** Riesgo de cada valle (agro.zonas): de la BD si está fresco (3 h); si no, Python lo calcula y Java lo graba. */
    @GetMapping("/mapa")
    public Map<String, Object> mapa(@RequestParam(defaultValue = "piura") String region,
                                    @RequestParam(defaultValue = "es") String lang) {
        ErroresApi.validarLang(lang);
        var zonas = catalogo.zonas("todas".equals(region) ? null : region);
        List<CompletableFuture<Map<String, Object>>> tareas = new ArrayList<>();
        // El Niño es el mismo para toda la costa: no pinta los valles, se manda una vez como aviso del mapa
        AtomicReference<Object> elNino = new AtomicReference<>();
        for (var z : zonas) {
            tareas.add(CompletableFuture.supplyAsync(() -> {
                String nivel = null;
                try {
                    // v2: desde el 15-nov el nivel del valle no incluye El Niño (las filas viejas no se reutilizan)
                    Respuesta r = reco.primeroBd("mapa", "zona:v2:" + z.id() + ":" + lang, Duration.ofHours(3), z.lat(), z.lon(), z.id(),
                            () -> calculos.indicadoresPunto(z.lat(), z.lon(), lang));
                    nivel = (String) r.datos().get("nivel");
                    if (r.datos().get("elNino") != null) elNino.compareAndSet(null, r.datos().get("elNino"));
                } catch (Exception ex) {
                    log.warn("Zona {} sin dato: {}", z.nombre(), ex.getMessage());   // sin dato: se dibuja gris (nivel null)
                }
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("nombre", z.nombre());
                m.put("lat", z.lat());
                m.put("lon", z.lon());
                m.put("nivel", nivel == null || nivel.isBlank() ? null : nivel);
                return m;
            }));
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("region", region);
        out.put("zonas", tareas.stream().map(CompletableFuture::join).toList());
        out.put("elNino", elNino.get());
        return out;
    }

    @GetMapping("/cultivos")
    public List<Map<String, Object>> cultivos(@RequestParam(defaultValue = "es") String lang) {
        ErroresApi.validarLang(lang);
        return catalogo.cultivos(null, false).stream().map(c -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", c.id());
            m.put("nombre", "en".equals(lang) ? NombresCultivo.en(c.nombre()) : NombresCultivo.es(c.nombre()));
            m.put("usoAgua", switch (c.agua()) { case "baja" -> "bajo"; case "alta" -> "alto"; default -> "medio"; });
            m.put("toleranciaCalor", c.tempMax() >= 35 ? "alto" : c.tempMax() >= 30 ? "medio" : "bajo");
            m.put("toleranciaSequia", c.toleraSequia() ? "alto" : "bajo");
            m.put("cicloDias", c.cicloDias() == null ? 365 : c.cicloDias());
            return m;
        }).toList();
    }

    // ------------------------------------------------------------------ ¿Funciona? (máquina del tiempo)
    /** Años con datos reales (los decide el servicio de cálculos: IMERG en Piura, NASA POWER fuera). */
    @GetMapping("/validacion/anios")
    public Map<String, Object> anios(@RequestParam(defaultValue = "-5.19") double lat, @RequestParam(defaultValue = "-80.63") double lon) {
        ErroresApi.validarCoordenadas(lat, lon);
        return calculos.anios(lat, lon);
    }

    /** Todos los años desde 2016: aciertos, falsas alarmas y eventos no avisados. Se guarda 6 h (incluye el año en curso). */
    @GetMapping("/validacion/resumen")
    public ResponseEntity<Map<String, Object>> resumenValidacion(@RequestParam(defaultValue = "-5.19") double lat,
                                                                 @RequestParam(defaultValue = "-80.63") double lon,
                                                                 @RequestParam(defaultValue = "es") String lang) {
        ErroresApi.validarCoordenadas(lat, lon);
        ErroresApi.validarLang(lang);
        String clave = String.format(Locale.ROOT, "valres:%.3f,%.3f:%s", lat, lon, lang);
        return responder(reco.primeroBd("validacion_resumen", clave, Duration.ofHours(6), lat, lon, null,
                () -> calculos.resumenValidacion(lat, lon, lang)));
    }

    /** Datos históricos: se guardan 30 días en la BD (no cambian). */
    @GetMapping("/validacion")
    public ResponseEntity<Map<String, Object>> validacion(@RequestParam int anio, @RequestParam double lat, @RequestParam double lon,
                                                          @RequestParam(defaultValue = "es") String lang) {
        ErroresApi.validarCoordenadas(lat, lon);
        ErroresApi.validarLang(lang);
        String clave = String.format(Locale.ROOT, "val:%d:%.3f,%.3f:%s", anio, lat, lon, lang);
        return responder(reco.primeroBd("validacion", clave, frescuraAnio(anio), lat, lon, null,
                () -> calculos.validacion(anio, lat, lon, lang)));
    }

    /** Lluvia de un mes día por día y por semana (clic en una barra de "¿Funciona?"). Se guarda en la BD. */
    @GetMapping("/validacion/detalle")
    public ResponseEntity<Map<String, Object>> detalleLluvia(@RequestParam int anio, @RequestParam int mes,
                                                             @RequestParam double lat, @RequestParam double lon) {
        ErroresApi.validarCoordenadas(lat, lon);
        if (mes < 1 || mes > 12 || anio < 2001 || anio > 2100) {
            throw new org.springframework.web.server.ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST, "anio o mes fuera de rango");
        }
        String clave = String.format(Locale.ROOT, "valdia:%d-%02d:%.3f,%.3f", anio, mes, lat, lon);
        return responder(reco.primeroBd("validacion_dia", clave, frescuraMes(anio, mes), lat, lon, null,
                () -> calculos.detalleLluvia(anio, mes, lat, lon)));
    }

    /** El año en curso cambia cada día (IMERG Late): 6 h. Años cerrados: 30 días. */
    static Duration frescuraAnio(int anio) {
        return anio >= java.time.LocalDate.now(java.time.ZoneId.of("America/Lima")).getYear() ? Duration.ofHours(6) : Duration.ofDays(30);
    }

    /** Meses de los últimos 60 días aún pueden completarse (IMERG Late): 6 h. Meses viejos: 30 días. */
    static Duration frescuraMes(int anio, int mes) {
        var hoy = java.time.LocalDate.now(java.time.ZoneId.of("America/Lima"));
        return java.time.YearMonth.of(anio, mes).atEndOfMonth().isAfter(hoy.minusDays(60)) ? Duration.ofHours(6) : Duration.ofDays(30);
    }

    /** Respuesta tal cual; si vino del respaldo: X-Desde-Cache: true y X-Fecha-Dato (fecha del cálculo guardado). */
    static ResponseEntity<Map<String, Object>> responder(Respuesta r) {
        ResponseEntity.BodyBuilder ok = ResponseEntity.ok();
        if (r.desdeCache()) {
            ok.header("X-Desde-Cache", "true");
            Object fecha = r.datos().get("fecha");
            if (fecha != null) ok.header("X-Fecha-Dato", fecha.toString());
        }
        return ok.body(r.datos());
    }
}
