package pe.halcondorado.allpashift.api;

import java.time.Duration;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Cultivo;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Zona;
import pe.halcondorado.allpashift.catalogo.ConsultasRepository;

/**
 * Flujo de la regla de arquitectura (doc 29):
 * 1) busca en PostgreSQL un resultado fresco; 2) si no hay, pide a climate-service (Python) que descargue los datos
 * NASA y calcule; 3) GRABA en PostgreSQL (consultas, datos_nasa, riesgo_mensual); 4) responde a la app.
 * Java no llama a la NASA.
 */
@Service
public class RecomendacionService {

    private static final Logger log = LoggerFactory.getLogger(RecomendacionService.class);
    private static final Map<String, String> PERMANENTES = Map.of("mango", "Mango", "limon", "Limon", "banano", "Banano organico");
    public static final Duration FRESCURA_RECOMENDACION = Duration.ofHours(3);

    private final CatalogoRepository catalogo;
    private final ConsultasRepository consultas;
    private final RestClient python;
    private final JsonUtil json;

    public RecomendacionService(CatalogoRepository catalogo, ConsultasRepository consultas, JsonUtil json,
                                @Value("${CLIMATE_SERVICE_URL:http://localhost:8000}") String climateUrl) {
        this.catalogo = catalogo;
        this.consultas = consultas;
        this.json = json;
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        f.setConnectTimeout(Duration.ofSeconds(5));
        f.setReadTimeout(Duration.ofSeconds(90));
        this.python = RestClient.builder().baseUrl(climateUrl).requestFactory(f).build();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> llamarPython(String ruta, Object cuerpo) {
        return python.post().uri(ruta).contentType(MediaType.APPLICATION_JSON).body(cuerpo).retrieve().body(Map.class);
    }

    public Zona zonaCercana(double lat, double lon, double maxGrados2) {
        Zona mejor = null;
        double dist = Double.MAX_VALUE;
        for (Zona z : catalogo.zonas(null)) {
            double d = Math.pow(z.lat() - lat, 2) + Math.pow(z.lon() - lon, 2);
            if (d < dist) { dist = d; mejor = z; }
        }
        return dist <= maxGrados2 ? mejor : null;
    }

    public String pisoDe(double lat, double lon) {
        Zona z = zonaCercana(lat, lon, 0.5);
        return z != null ? z.piso() : "costa";
    }

    /** GET /api/recomendacion: primero PostgreSQL; si no hay dato fresco, Python calcula y Java graba. */
    @SuppressWarnings("unchecked")
    public Map<String, Object> recomendacion(double lat, double lon, String tipoCultivo, String mesSiembra, String cultivo) {
        String tipo = "permanente".equals(tipoCultivo) ? "permanente" : "temporal";
        String mes = mesSiembra == null || mesSiembra.isBlank() ? LocalDate.now().toString().substring(0, 7) : mesSiembra;
        String clave = String.format(Locale.ROOT, "reco:%.3f,%.3f:%s:%s", lat, lon, tipo, "permanente".equals(tipo) ? cultivo : mes);

        var guardada = consultas.buscar(clave, FRESCURA_RECOMENDACION);
        if (guardada != null) return json.leer(guardada.resultado());

        String piso = pisoDe(lat, lon);
        Map<String, Object> pedido = new LinkedHashMap<>();
        pedido.put("lat", lat);
        pedido.put("lon", lon);
        pedido.put("tipoCultivo", tipo);
        Map<Integer, Integer> rotC1 = new HashMap<>();
        if ("permanente".equals(tipo)) {
            String nombre = PERMANENTES.getOrDefault(cultivo == null ? "mango" : cultivo, "Mango");
            Integer id = catalogo.idCultivo(nombre);
            String cal = id == null ? null : catalogo.calendario(id, piso);
            if (cal == null && id != null) cal = catalogo.calendario(id, "costa");
            List<Map<String, Object>> acciones = new ArrayList<>();
            if (id != null) catalogo.acciones(id).forEach(a -> acciones.add(Map.of("fase", a.fase(), "descripcion", a.descripcion(), "alerta", a.alerta() == null ? "" : a.alerta())));
            pedido.put("permanente", Map.of("nombre", nombre, "calendario", cal == null ? "CCCCCCCCCCCC" : cal, "fases", catalogo.fases(), "acciones", acciones));
        } else {
            List<Cultivo> cultivos = catalogo.cultivos(piso, true);
            pedido.put("mesSiembra", mes);
            pedido.put("cultivos", cultivos.stream().map(c -> {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("id", c.id()); m.put("nombre", c.nombre()); m.put("tempMinC", c.tempMin()); m.put("tempMaxC", c.tempMax());
                m.put("aguaNecesaria", c.agua()); m.put("mesesSiembra", c.mesesSiembra()); m.put("mesesCosecha", c.mesesCosecha());
                m.put("cicloDias", c.cicloDias()); m.put("toleraSequia", c.toleraSequia()); m.put("toleraInundacion", c.toleraInundacion());
                return m;
            }).toList());
            List<Integer> ids = cultivos.stream().map(Cultivo::id).toList();
            var rots = catalogo.rotaciones(piso).stream().filter(r -> ids.contains(r.cultivo1Id()) && ids.contains(r.cultivo2Id())).toList();
            if (!rots.isEmpty()) {
                pedido.put("rotaciones", rots.stream().map(r -> Map.of("id", r.id(), "nombre", r.nombre(), "cultivo1Id", r.cultivo1Id(), "cultivo2Id", r.cultivo2Id())).toList());
                rots.stream().filter(CatalogoRepository.Rotacion::monocultivo).findFirst().ifPresent(r -> pedido.put("rotacionActualId", r.id()));
                rots.forEach(r -> rotC1.put(r.id(), r.cultivo1Id()));
            }
        }

        Map<String, Object> py = llamarPython("/calcular", pedido);
        Map<String, Object> reco = (Map<String, Object>) py.get("recomendacion");
        guardar(clave, lat, lon, reco, py, rotC1);
        return reco;
    }

    /** Graba la consulta, los datos NASA y la perspectiva de la campaña (solo Java escribe en la BD). */
    @SuppressWarnings("unchecked")
    private void guardar(String clave, double lat, double lon, Map<String, Object> reco, Map<String, Object> py, Map<Integer, Integer> rotC1) {
        try {
            Zona zona = zonaCercana(lat, lon, 0.09);   // ~30 km: solo se asocia si el punto está en un valle conocido
            Integer zonaId = zona == null ? null : zona.id();
            List<Map<String, Object>> rots = (List<Map<String, Object>>) reco.getOrDefault("rotaciones", List.of());
            Integer mejorId = rots.isEmpty() ? null : ((Number) rots.get(0).get("id")).intValue();
            consultas.guardar("recomendacion", clave, lat, lon, zonaId, mejorId, json.escribir(reco.get("indicadores")), json.escribir(reco),
                    py.get("contrato") == null ? null : json.escribir(py.get("contrato")), (List<Map<String, Object>>) py.get("datosNasa"));
            if (zonaId != null && mejorId != null && rotC1.containsKey(mejorId) && rots.get(0).get("ciclo") instanceof Map<?, ?> ciclo) {
                for (Map<String, Object> m : (List<Map<String, Object>>) ciclo.get("meses")) {
                    String ym = (String) m.get("mes");
                    consultas.guardarRiesgoMes(zonaId, rotC1.get(mejorId), Integer.parseInt(ym.substring(0, 4)), Integer.parseInt(ym.substring(5, 7)),
                            (String) m.get("riesgo"), (String) m.get("motivo"));
                }
            }
        } catch (Exception e) {
            log.warn("No se pudo grabar la consulta {}: {}", clave, e.getMessage());   // la app igual recibe su respuesta
        }
    }

    /** Respuesta en forma del contrato guardada en la BD (para el asistente). */
    public Map<String, Object> contratoGuardado(double lat, double lon, String mes) {
        String clave = String.format(Locale.ROOT, "reco:%.3f,%.3f:temporal:%s", lat, lon, mes);
        var g = consultas.buscar(clave, FRESCURA_RECOMENDACION);
        if (g == null || g.contrato() == null) {
            recomendacion(lat, lon, "temporal", mes, null);
            g = consultas.buscar(clave, FRESCURA_RECOMENDACION);
        }
        return g == null || g.contrato() == null ? null : json.leer(g.contrato());
    }
}
