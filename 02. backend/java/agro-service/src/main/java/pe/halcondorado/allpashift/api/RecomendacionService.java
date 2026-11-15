package pe.halcondorado.allpashift.api;

import java.time.Duration;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Supplier;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import pe.halcondorado.allpashift.calculos.CalculosClient;
import pe.halcondorado.allpashift.calculos.CalculosClient.CalculosNoDisponibleException;
import pe.halcondorado.allpashift.calculos.CatalogoCalculos;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Zona;
import pe.halcondorado.allpashift.catalogo.ConsultasRepository;

/**
 * Flujo de la regla de arquitectura (doc 29):
 * 1) busca en PostgreSQL un resultado fresco; 2) si no hay, pide al servicio de cálculos (Python) que descargue los
 * datos NASA y calcule, enviándole el catálogo leído de la BD; 3) GRABA en PostgreSQL (consultas, riesgo_mensual);
 * 4) responde a la app. Si Python falla, responde el último resultado guardado (aunque sea viejo) marcado
 * "desdeCache"; si no hay nada guardado, lanza CalculosNoDisponibleException (→ 503). Nunca inventa datos.
 */
@Service
public class RecomendacionService {

    private static final Logger log = LoggerFactory.getLogger(RecomendacionService.class);
    /** Cultivos permanentes que pide la app → nombre en agro.cultivos. */
    private static final Map<String, String> PERMANENTES = Map.of("mango", "Mango", "limon", "Limon", "banano", "Banano organico");
    public static final Duration FRESCURA_RECOMENDACION = Duration.ofHours(3);
    /** Para el respaldo: cualquier resultado guardado sirve si Python no responde. */
    static final Duration CUALQUIER_EDAD = Duration.ofDays(3650);

    /** Respuesta para la app y si vino del respaldo (Python caído). */
    public record Respuesta(Map<String, Object> datos, boolean desdeCache) {}

    private final CatalogoRepository catalogo;
    private final ConsultasRepository consultas;
    private final CalculosClient calculos;
    private final CatalogoCalculos catalogoCalculos;
    private final JsonUtil json;

    public RecomendacionService(CatalogoRepository catalogo, ConsultasRepository consultas, JsonUtil json,
                                CalculosClient calculos, CatalogoCalculos catalogoCalculos) {
        this.catalogo = catalogo;
        this.consultas = consultas;
        this.json = json;
        this.calculos = calculos;
        this.catalogoCalculos = catalogoCalculos;
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

    /**
     * Primero la BD (fresco); si no, calcula y graba; si Python falla, lo último guardado; si no hay, excepción.
     * Lo usan /api/recomendacion, /api/mapa, /api/validacion y el asistente.
     */
    public Respuesta primeroBd(String tipo, String clave, Duration frescura, double lat, double lon, Integer zonaId,
                               Supplier<Map<String, Object>> calcular) {
        var guardada = consultas.buscar(clave, frescura);
        if (guardada != null) return new Respuesta(json.leer(guardada.resultado()), false);
        try {
            Map<String, Object> nuevo = calcular.get();
            try {
                // datosNasa: valores NASA que usó Python (SMAP, IMERG, MUR SST, NDVI, POWER) → nasa.datos_nasa
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> datosNasa = nuevo.get("datosNasa") instanceof List<?> l ? (List<Map<String, Object>>) l : null;
                consultas.guardar(tipo, clave, lat, lon, zonaId, null, json.escribir(nuevo.get("indicadores")),
                        json.escribir(nuevo), null, datosNasa);
            } catch (Exception e) {
                log.warn("No se pudo grabar {} {}: {}", tipo, clave, e.getMessage());   // la app igual recibe su respuesta
            }
            return new Respuesta(nuevo, false);
        } catch (CalculosNoDisponibleException e) {
            var vieja = consultas.buscar(clave, CUALQUIER_EDAD);
            if (vieja != null) {
                log.warn("Servicio de cálculos no disponible ({}): respaldo desde la BD para {}", e.getMessage(), clave);
                return new Respuesta(json.leer(vieja.resultado()), true);
            }
            throw e;
        }
    }

    /** GET /api/recomendacion */
    @SuppressWarnings("unchecked")
    public Respuesta recomendacion(double lat, double lon, String lang, String tipoCultivo, String mesSiembra, String cultivo) {
        return recomendacion(lat, lon, lang, tipoCultivo, mesSiembra, cultivo, PerfilAgricultor.VACIO);
    }

    /** GET /api/recomendacion con la prioridad y el suelo que eligió el agricultor (solo afectan a las rotaciones). */
    @SuppressWarnings("unchecked")
    public Respuesta recomendacion(double lat, double lon, String lang, String tipoCultivo, String mesSiembra, String cultivo,
                                   PerfilAgricultor perfil) {
        String idioma = "en".equals(lang) ? "en" : "es";
        String tipo = "permanente".equals(tipoCultivo) ? "permanente" : "temporal";
        String mes = mesSiembra == null || mesSiembra.isBlank()
                ? LocalDate.now(ZoneId.of("America/Lima")).toString().substring(0, 7) : mesSiembra;
        String perm = cultivo == null || cultivo.isBlank() ? "mango" : cultivo;
        PerfilAgricultor pf = perfil == null ? PerfilAgricultor.VACIO : perfil;
        String clave = String.format(Locale.ROOT, "reco:%.3f,%.3f:%s:%s:%s", lat, lon, tipo, "permanente".equals(tipo) ? perm : mes, idioma)
                + ("permanente".equals(tipo) ? "" : ":v2:" + pf.clave());   // v2: rotaciones con suelo y prioridad (15-nov)
        Zona zona = zonaCercana(lat, lon, 0.09);   // ~30 km: solo se asocia si el punto está en un valle conocido
        Integer zonaId = zona == null ? null : zona.id();

        return primeroBd("recomendacion", clave, FRESCURA_RECOMENDACION, lat, lon, zonaId, () -> {
            var cat = catalogoCalculos.paraPiso(pisoDe(lat, lon));
            Map<String, Object> pedido = new LinkedHashMap<>();
            pedido.put("lat", lat);
            pedido.put("lon", lon);
            pedido.put("lang", idioma);
            pedido.put("tipoCultivo", tipo);
            if ("permanente".equals(tipo)) {
                pedido.put("cultivo", CatalogoCalculos.codigo(PERMANENTES.getOrDefault(perm, perm)));
            } else {
                pedido.put("mesSiembra", mes);
                pf.ponerEn(pedido);
            }
            pedido.put("catalogo", cat.cultivos());
            Map<String, Object> reco = calculos.calcular(pedido);
            if (zonaId != null) grabarRiesgoMensual(zonaId, reco, cat.idPorCodigo());
            return reco;
        });
    }

    /** Perspectiva de la campaña de la mejor rotación → agro.riesgo_mensual (solo Java escribe en la BD). */
    @SuppressWarnings("unchecked")
    private void grabarRiesgoMensual(int zonaId, Map<String, Object> reco, Map<String, Integer> idPorCodigo) {
        try {
            List<Map<String, Object>> rots = (List<Map<String, Object>>) reco.getOrDefault("rotaciones", List.of());
            if (rots.isEmpty() || !(rots.get(0).get("ciclo") instanceof Map<?, ?> ciclo)) return;
            for (Map<String, Object> m : (List<Map<String, Object>>) ciclo.get("meses")) {
                Integer cultivoId = idPorCodigo.get((String) m.get("cultivo"));
                if (cultivoId == null) continue;
                String ym = (String) m.get("mes");
                consultas.guardarRiesgoMes(zonaId, cultivoId, Integer.parseInt(ym.substring(0, 4)), Integer.parseInt(ym.substring(5, 7)),
                        (String) m.get("riesgo"), (String) m.get("motivo"));
            }
        } catch (Exception e) {
            log.warn("No se pudo grabar el riesgo mensual: {}", e.getMessage());
        }
    }
}
