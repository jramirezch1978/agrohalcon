package pe.halcondorado.allpashift.api;

import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.nasa.NasaService;

/** API que consume la app (frontend de Sheila, modo "java"): GET /api/recomendacion, /api/mapa, /api/validacion... */
@RestController
@RequestMapping("/api")
public class ApiController {

    private static final Logger log = LoggerFactory.getLogger(ApiController.class);

    private final RecomendacionService reco;
    private final CatalogoRepository catalogo;
    private final NasaService nasa;
    private final RestClient climate;
    private final Map<String, Object[]> cacheMapa = new ConcurrentHashMap<>();

    public ApiController(RecomendacionService reco, CatalogoRepository catalogo, NasaService nasa,
                         @org.springframework.beans.factory.annotation.Value("${CLIMATE_SERVICE_URL:http://localhost:8000}") String climateUrl) {
        this.reco = reco;
        this.catalogo = catalogo;
        this.nasa = nasa;
        var f = new org.springframework.http.client.SimpleClientHttpRequestFactory();
        f.setConnectTimeout(java.time.Duration.ofSeconds(5));
        f.setReadTimeout(java.time.Duration.ofSeconds(30));
        this.climate = RestClient.builder().baseUrl(climateUrl).requestFactory(f).build();
    }

    @GetMapping("/recomendacion")
    public Map<String, Object> recomendacion(@RequestParam double lat, @RequestParam double lon,
                                             @RequestParam(required = false) String tipoCultivo,
                                             @RequestParam(required = false) String mesSiembra,
                                             @RequestParam(required = false) String cultivo) {
        return reco.recomendacion(lat, lon, tipoCultivo, mesSiembra, cultivo);
    }

    /** Riesgo de cada valle de la región (máximo nivel de sus indicadores), calculado por climate-service. */
    @GetMapping("/mapa")
    @SuppressWarnings("unchecked")
    public Map<String, Object> mapa(@RequestParam(defaultValue = "piura") String region) {
        Object[] c = cacheMapa.get(region);
        if (c != null && (long) c[1] > System.currentTimeMillis()) return (Map<String, Object>) c[0];
        var zonas = catalogo.zonas("todas".equals(region) ? null : region);
        List<CompletableFuture<Map<String, Object>>> tareas = new ArrayList<>();
        for (var z : zonas) {
            tareas.add(CompletableFuture.supplyAsync(() -> {
                String nivel = null;
                try {
                    var e = reco.entradaNasa(z.lat(), z.lon());
                    Map<String, Object> ind = climate.post().uri("/indicadores").contentType(MediaType.APPLICATION_JSON).body(e.cuerpo()).retrieve().body(Map.class);
                    if (e.sst() == null) ind.remove("elNino");
                    int peor = -1;
                    for (Object v : ind.values()) {
                        String n = (String) ((Map<String, Object>) v).get("nivel");
                        peor = Math.max(peor, "alto".equals(n) ? 2 : "medio".equals(n) ? 1 : 0);
                    }
                    nivel = peor == 2 ? "alto" : peor == 1 ? "medio" : peor == 0 ? "bajo" : null;
                } catch (Exception ex) {
                    log.warn("Zona {} sin dato: {}", z.nombre(), ex.getMessage());
                }
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("nombre", z.nombre());
                m.put("lat", z.lat());
                m.put("lon", z.lon());
                m.put("nivel", nivel);
                return m;
            }));
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("region", region);
        out.put("zonas", tareas.stream().map(CompletableFuture::join).toList());
        cacheMapa.put(region, new Object[]{out, System.currentTimeMillis() + 3 * 3600_000L});
        return out;
    }

    @GetMapping("/cultivos")
    public List<Map<String, Object>> cultivos() {
        return catalogo.cultivos(null, false).stream().map(c -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", c.id());
            m.put("nombre", c.nombre());
            m.put("usoAgua", switch (c.agua()) { case "baja" -> "bajo"; case "alta" -> "alto"; default -> "medio"; });
            m.put("toleranciaCalor", c.tempMax() >= 35 ? "alto" : c.tempMax() >= 30 ? "medio" : "bajo");
            m.put("toleranciaSequia", c.toleraSequia() ? "alto" : "bajo");
            m.put("cicloDias", c.cicloDias() == null ? 365 : c.cicloDias());
            return m;
        }).toList();
    }

    /** Asistente sin IA: plantillas de climate-service sobre la recomendación ya calculada. */
    @PostMapping("/asistente")
    @SuppressWarnings("unchecked")
    public Map<String, Object> asistente(@RequestBody Map<String, Object> cuerpo) {
        double lat = ((Number) cuerpo.get("lat")).doubleValue(), lon = ((Number) cuerpo.get("lon")).doubleValue();
        String idioma = (String) cuerpo.getOrDefault("idioma", "es");
        var e = reco.entradaNasa(lat, lon);
        Map<String, Object> py = reco.recomendacionPython(lat, lon, reco.pisoDe(lat, lon), e);
        Map<String, Object> pedido = Map.of("respuesta", "", "idioma", idioma, "recomendacion", py);
        Map<String, Object> r = climate.post().uri("/asistente/plan-b").contentType(MediaType.APPLICATION_JSON).body(pedido).retrieve().body(Map.class);
        return Map.of("respuesta", r.get("respuesta"), "fuentes", r.getOrDefault("fuentes", List.of()));
    }

    // ------------------------------------------------------------------ ¿Funciona? (máquina del tiempo)
    @GetMapping("/validacion/anios")
    public Map<String, Object> anios(@RequestParam double lat, @RequestParam double lon) {
        List<Integer> anios = new ArrayList<>(List.of(1998, 2017, 2023));
        int ultimo = LocalDate.now().getYear() - 1;
        if (!anios.contains(ultimo)) anios.add(ultimo);
        return Map.of("anios", anios, "fuente", "NASA POWER", "conMurSst", anios.stream().filter(a -> a >= 2003).toList());
    }

    @GetMapping("/validacion")
    public Map<String, Object> validacion(@RequestParam int anio, @RequestParam double lat, @RequestParam double lon) {
        var serie = nasa.mensual(lat, lon, anio);
        var clim = nasa.climatologia(lat, lon);
        double[] ll = serie.get("PRECTOTCORR"), hum = serie.get("GWETROOT"), llN = clim.get("PRECTOTCORR"), humN = clim.get("GWETROOT");
        List<Double> valores = new ArrayList<>(), normal = new ArrayList<>(), hv = new ArrayList<>(), hn = new ArrayList<>();
        int max = -1;
        Map<String, Object> alerta = null;
        for (int m = 0; m < 12; m++) {
            int dias = YearMonth.of(anio, m + 1).lengthOfMonth();
            Double v = Double.isNaN(ll[m]) ? null : Math.round(ll[m] * dias * 10) / 10.0;
            double n = Math.round(llN[m] * dias * 10) / 10.0;
            valores.add(v);
            normal.add(n);
            hv.add(Double.isNaN(hum[m]) ? null : Math.round(hum[m] * 100) / 100.0);
            hn.add(Math.round(humN[m] * 100) / 100.0);
            if (v != null && (max < 0 || v > valores.get(max))) max = m;
            if (alerta == null && v != null && v > Math.max(3 * n, 30)) {
                String fecha = String.format("%d-%02d-15", anio, m + 1);
                String motivo = String.format(Locale.ROOT, "En %s llovieron %.0f mm frente a %.0f mm normales (%.1f veces)", RecomendacionService.mesNombre(m), v, n, v / Math.max(n, 1));
                alerta = new LinkedHashMap<>();
                alerta.put("fecha", fecha);
                alerta.put("accion", "Preparar drenaje y no sembrar en zonas bajas");
                alerta.put("motivo", motivo);
                alerta.put("indicador", "lluvia");
                alerta.put("nivel", "alto");
                alerta.put("valor", v);
                alerta.put("fuente", "NASA POWER");
                alerta.put("alertaDrenaje", Map.of("fecha", fecha, "valor", v, "fuente", "NASA POWER"));
                alerta.put("nota", "Alerta calculada con la lluvia mensual de NASA POWER");
            }
        }
        Integer semanas = null;
        String mesMax = max >= 0 ? YearMonth.of(anio, max + 1).toString() : null;
        if (alerta != null && max >= 0) {
            LocalDate a = LocalDate.parse((String) alerta.get("fecha")), b = LocalDate.of(anio, max + 1, 15);
            semanas = (int) Math.max(0, java.time.temporal.ChronoUnit.WEEKS.between(a, b));
        }
        Map<String, Object> evento = null;
        for (var ev : catalogo.eventos()) {
            if (ev.inicio().getYear() <= anio && (ev.fin() == null || ev.fin().getYear() >= anio)) {
                evento = Map.of("nombre", ev.nombre(), "inicio", YearMonth.from(ev.inicio()).toString(),
                        "fin", ev.fin() == null ? YearMonth.now().toString() : YearMonth.from(ev.fin()).toString());
                break;
            }
        }
        Map<String, Object> realidad = switch (anio) {
            case 2017 -> Map.of("resumen", "El Niño Costero de 2017 causó inundaciones en Piura (desborde del río Piura el 27 de marzo) y miles de hectáreas perdidas.", "fuente", "INDECI / SENASA");
            case 1998 -> Map.of("resumen", "El Niño 1997-98 fue extraordinario: lluvias de hasta 16 mm/día en enero en Piura.", "fuente", "ENFEN");
            case 2023 -> Map.of("resumen", "El Niño costero de 2023 trajo calor y lluvias que afectaron mango y uva.", "fuente", "ENFEN");
            default -> null;
        };
        Map<String, Object> previa = new LinkedHashMap<>();
        previa.put("tipo", alerta != null ? "preparar drenaje" : "sembrar");
        previa.put("accion", alerta != null ? "Preparar drenaje y adelantar la cosecha" : "Sembrar con normalidad");
        previa.put("motivo", alerta != null ? (String) alerta.get("motivo") : "La lluvia del año estuvo dentro de lo normal");
        previa.put("fuente", "NASA POWER");
        Map<String, Object> series = new LinkedHashMap<>();
        series.put("lluvia", Map.of("unidad", "mm/mes", "fuente", "NASA POWER", "valores", valores, "normal", normal, "producto", "POWER PRECTOTCORR"));
        series.put("humedadSuelo", Map.of("unidad", "fracción 0-1", "fuente", "NASA POWER", "valores", hv, "normal", hn, "producto", "POWER GWETROOT"));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("anio", anio);
        out.put("lat", lat);
        out.put("lon", lon);
        out.put("evento", evento);
        out.put("series", series);
        out.put("alerta", alerta);
        out.put("mesLluviaMaxima", mesMax);
        out.put("semanasAnticipacion", semanas);
        out.put("realidad", realidad);
        out.put("recomendacionPrevia", previa);
        out.put("resumen", alerta != null
                ? String.format("AllpaShift habría dado la alerta el %s, %d semanas antes del mes más lluvioso (%s).", alerta.get("fecha"), semanas == null ? 0 : semanas, mesMax)
                : "Ese año la lluvia no superó el umbral de alerta.");
        return out;
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> error(Exception e) {
        log.error("Error en la API", e);
        return ResponseEntity.status(502).body(Map.of("error", "No se pudo calcular: " + e.getMessage()));
    }
}
