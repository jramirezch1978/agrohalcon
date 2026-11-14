package pe.halcondorado.allpashift.api;

import java.time.Duration;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.ConsultasRepository;

/**
 * API que consume la app (web y móvil). Regla (doc 29): Java lee primero PostgreSQL; si no hay dato fresco,
 * Python descarga de la NASA y calcula, y Java graba el resultado. Java no llama a la NASA.
 */
@RestController
@RequestMapping("/api")
public class ApiController {

    private static final Logger log = LoggerFactory.getLogger(ApiController.class);

    private final RecomendacionService reco;
    private final CatalogoRepository catalogo;
    private final ConsultasRepository consultas;
    private final JsonUtil json;

    public ApiController(RecomendacionService reco, CatalogoRepository catalogo, ConsultasRepository consultas, JsonUtil json) {
        this.reco = reco;
        this.catalogo = catalogo;
        this.consultas = consultas;
        this.json = json;
    }

    @GetMapping("/recomendacion")
    public Map<String, Object> recomendacion(@RequestParam double lat, @RequestParam double lon,
                                             @RequestParam(required = false) String tipoCultivo,
                                             @RequestParam(required = false) String mesSiembra,
                                             @RequestParam(required = false) String cultivo) {
        return reco.recomendacion(lat, lon, tipoCultivo, mesSiembra, cultivo);
    }

    /** Riesgo de cada valle: de la BD si está fresco (3 h); si no, Python lo calcula y Java lo graba. */
    @GetMapping("/mapa")
    @SuppressWarnings("unchecked")
    public Map<String, Object> mapa(@RequestParam(defaultValue = "piura") String region) {
        var zonas = catalogo.zonas("todas".equals(region) ? null : region);
        List<CompletableFuture<Map<String, Object>>> tareas = new ArrayList<>();
        for (var z : zonas) {
            tareas.add(CompletableFuture.supplyAsync(() -> {
                String clave = "zona:" + z.id();
                String nivel = null;
                try {
                    var g = consultas.buscar(clave, Duration.ofHours(3));
                    if (g != null) {
                        nivel = (String) json.leer(g.resultado()).get("nivel");
                    } else {
                        Map<String, Object> py = reco.llamarPython("/indicadores-punto", Map.of("lat", z.lat(), "lon", z.lon()));
                        nivel = (String) py.get("nivel");
                        consultas.guardar("mapa", clave, z.lat(), z.lon(), z.id(), null, json.escribir(py.get("indicadores")),
                                json.escribir(Map.of("nivel", nivel == null ? "" : nivel)), null, (List<Map<String, Object>>) py.get("datosNasa"));
                    }
                } catch (Exception ex) {
                    log.warn("Zona {} sin dato: {}", z.nombre(), ex.getMessage());
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

    /** Asistente sin IA: plantillas de climate-service sobre la recomendación guardada en la BD. */
    @PostMapping("/asistente")
    public Map<String, Object> asistente(@RequestBody Map<String, Object> cuerpo) {
        double lat = ((Number) cuerpo.get("lat")).doubleValue(), lon = ((Number) cuerpo.get("lon")).doubleValue();
        String mes = (String) cuerpo.getOrDefault("mesSiembra", LocalDate.now().toString().substring(0, 7));
        Map<String, Object> contrato = reco.contratoGuardado(lat, lon, mes);
        if (contrato == null) return Map.of("respuesta", "Primero calcula la recomendación de tu parcela.", "fuentes", List.of());
        Map<String, Object> r = reco.llamarPython("/asistente/plan-b",
                Map.of("respuesta", "", "idioma", cuerpo.getOrDefault("idioma", "es"), "recomendacion", contrato));
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

    /** Datos históricos: se guardan 30 días en la BD (no cambian). */
    @GetMapping("/validacion")
    public Map<String, Object> validacion(@RequestParam int anio, @RequestParam double lat, @RequestParam double lon) {
        String clave = String.format(Locale.ROOT, "val:%d:%.3f,%.3f", anio, lat, lon);
        var g = consultas.buscar(clave, Duration.ofDays(30));
        if (g != null) return json.leer(g.resultado());
        List<Map<String, Object>> eventos = catalogo.eventos().stream().map(e -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("nombre", e.nombre());
            m.put("inicio", e.inicio().toString());
            if (e.fin() != null) m.put("fin", e.fin().toString());
            return m;
        }).toList();
        Map<String, Object> v = reco.llamarPython("/validacion", Map.of("anio", anio, "lat", lat, "lon", lon, "eventos", eventos));
        try {
            consultas.guardar("validacion", clave, lat, lon, null, null, null, json.escribir(v), null, null);
        } catch (Exception e) {
            log.warn("No se pudo grabar la validación: {}", e.getMessage());
        }
        return v;
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> error(Exception e) {
        log.error("Error en la API", e);
        return ResponseEntity.status(502).body(Map.of("error", "No se pudo calcular: " + e.getMessage()));
    }
}
