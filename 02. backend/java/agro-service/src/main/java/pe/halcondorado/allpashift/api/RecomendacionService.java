package pe.halcondorado.allpashift.api;

import java.time.Duration;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Cultivo;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Zona;
import pe.halcondorado.allpashift.nasa.NasaService;
import pe.halcondorado.allpashift.nasa.NasaService.Climatologia;
import pe.halcondorado.allpashift.nasa.NasaService.Reciente;

/**
 * Orquesta la recomendación (contrato del backend):
 * 1) descarga los datos NASA del punto, 2) lee el catálogo de PostgreSQL,
 * 3) llama a climate-service (David) que calcula indicadores, rotaciones y "qué hacer",
 * 4) completa lo que la app muestra: uso de agua, perspectiva de la campaña y plan de cultivos permanentes.
 */
@Service
public class RecomendacionService {

    private static final String[] MES_NOMBRE = {"enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"};
    private static final Map<String, String> PERMANENTES = Map.of("mango", "Mango", "limon", "Limon", "banano", "Banano organico");

    private final NasaService nasa;
    private final CatalogoRepository catalogo;
    private final RestClient climate;
    private final Map<String, Object[]> cache = new ConcurrentHashMap<>();

    public RecomendacionService(NasaService nasa, CatalogoRepository catalogo, @Value("${CLIMATE_SERVICE_URL:http://localhost:8000}") String climateUrl) {
        this.nasa = nasa;
        this.catalogo = catalogo;
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        f.setConnectTimeout(Duration.ofSeconds(5));
        f.setReadTimeout(Duration.ofSeconds(30));
        this.climate = RestClient.builder().baseUrl(climateUrl).requestFactory(f).build();
    }

    /** Datos NASA del punto en el formato de entrada de climate-service. */
    public record EntradaNasa(Map<String, Object> cuerpo, Climatologia clim, Reciente rec, Double sst) {}

    public EntradaNasa entradaNasa(double lat, double lon) {
        Climatologia clim = nasa.climatologia(lat, lon);
        Reciente rec = nasa.reciente(lat, lon);
        Double sst = nasa.sstAnomalia(lat, lon);
        int m = LocalDate.now().getMonthValue() - 1;
        double lluviaN = clim.get("PRECTOTCORR")[m], humN = clim.get("GWETTOP")[m], tmaxN = clim.get("T2M_MAX")[m], tminN = clim.get("T2M_MIN")[m];
        Map<String, Object> actual = new LinkedHashMap<>();
        actual.put("lluviaMm", rec != null ? r2(rec.lluviaMmDia()) : r2(lluviaN));
        actual.put("humedadSuelo", rec != null ? r3(rec.humedadSup()) : r3(humN));
        actual.put("tempMaxC", rec != null ? r1(rec.tMax()) : r1(tmaxN));
        actual.put("tempMinC", rec != null ? r1(rec.tMin()) : r1(tminN));
        actual.put("sstAnomaliaC", sst != null ? r2(sst) : 0.0);
        Map<String, Object> historico = Map.of("lluviaMm", r2(lluviaN), "humedadSuelo", r3(humN), "tempMaxC", r1(tmaxN), "tempMinC", r1(tminN));
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("lluvia", Map.of("fuente", "NASA POWER", "unidad", "mm/día"));
        meta.put("humedadSuelo", Map.of("fuente", "NASA POWER", "unidad", "fracción 0-1"));
        meta.put("calor", Map.of("fuente", "NASA POWER", "unidad", "°C"));
        meta.put("elNino", Map.of("fuente", sst != null ? "MUR SST" : "sin dato", "unidad", "°C anomalía"));
        Map<String, Object> cuerpo = new LinkedHashMap<>();
        cuerpo.put("lat", lat);
        cuerpo.put("lon", lon);
        cuerpo.put("actual", actual);
        cuerpo.put("historico", historico);
        cuerpo.put("meta", meta);
        return new EntradaNasa(cuerpo, clim, rec, sst);
    }

    public String pisoDe(double lat, double lon) {
        Zona mejor = null;
        double dist = Double.MAX_VALUE;
        for (Zona z : catalogo.zonas(null)) {
            double d = Math.pow(z.lat() - lat, 2) + Math.pow(z.lon() - lon, 2);
            if (d < dist) { dist = d; mejor = z; }
        }
        return mejor != null && dist < 0.5 ? mejor.piso() : "costa";
    }

    /** Respuesta de climate-service (/recomendacion) tal cual; la usa también el asistente. */
    @SuppressWarnings("unchecked")
    public Map<String, Object> recomendacionPython(double lat, double lon, String piso, EntradaNasa e) {
        List<Cultivo> cultivos = catalogo.cultivos(piso, true);
        Map<String, Object> cuerpo = new LinkedHashMap<>(e.cuerpo());
        cuerpo.put("fecha", LocalDate.now().toString());
        cuerpo.put("cultivos", cultivos.stream().map(c -> Map.of("id", c.id(), "nombre", c.nombre(), "tempMinC", c.tempMin(), "tempMaxC", c.tempMax(),
                "aguaNecesaria", c.agua(), "mesesSiembra", c.mesesSiembra(), "mesesCosecha", c.mesesCosecha())).toList());
        List<Integer> ids = cultivos.stream().map(Cultivo::id).toList();
        var rots = catalogo.rotaciones(piso).stream().filter(r -> ids.contains(r.cultivo1Id()) && ids.contains(r.cultivo2Id())).toList();
        if (!rots.isEmpty()) {
            cuerpo.put("rotaciones", rots.stream().map(r -> Map.of("id", r.id(), "nombre", r.nombre(), "cultivo1Id", r.cultivo1Id(), "cultivo2Id", r.cultivo2Id())).toList());
            rots.stream().filter(CatalogoRepository.Rotacion::monocultivo).findFirst().ifPresent(r -> cuerpo.put("rotacionActualId", r.id()));
        }
        cuerpo.put("top", 3);
        return climate.post().uri("/recomendacion").contentType(MediaType.APPLICATION_JSON).body(cuerpo).retrieve().body(Map.class);
    }

    /** GET /api/recomendacion: forma exacta que espera la app (types/api.ts → Recomendacion). */
    @SuppressWarnings("unchecked")
    public Map<String, Object> recomendacion(double lat, double lon, String tipoCultivo, String mesSiembra, String cultivo) {
        String clave = String.format(Locale.ROOT, "%.3f,%.3f,%s,%s,%s", lat, lon, tipoCultivo, mesSiembra, cultivo);
        Object[] c = cache.get(clave);
        if (c != null && (long) c[1] > System.currentTimeMillis()) return (Map<String, Object>) c[0];

        String piso = pisoDe(lat, lon);
        EntradaNasa e = entradaNasa(lat, lon);
        Map<String, Object> py = recomendacionPython(lat, lon, piso, e);
        Map<String, Object> ind = new LinkedHashMap<>((Map<String, Object>) py.get("indicadores"));
        if (e.sst() == null) ind.remove("elNino");                   // nunca se muestra un dato que no existe
        ind.forEach((k, v) -> detalle(k, (Map<String, Object>) v));

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("lat", lat);
        out.put("lon", lon);
        out.put("fecha", py.get("fecha"));
        out.put("indicadores", ind);
        String nivelLluvia = nivel(ind, "lluvia"), nivelNino = nivel(ind, "elNino"), nivelHum = nivel(ind, "humedadSuelo");

        if ("permanente".equals(tipoCultivo)) {
            String nombre = PERMANENTES.getOrDefault(cultivo == null ? "mango" : cultivo, "Mango");
            Map<String, Object> plan = planPermanente(nombre, piso, e.clim(), nivelLluvia, nivelNino);
            out.put("rotaciones", List.of());
            out.put("plan", plan);
            out.put("queHacer", queHacerPermanente(nombre, plan, ind, nivelLluvia, nivelNino, nivelHum));
        } else {
            YearMonth siembra = mesSiembra != null && !mesSiembra.isBlank() ? YearMonth.parse(mesSiembra) : YearMonth.now();
            Map<Integer, Cultivo> porId = new HashMap<>();
            catalogo.cultivos(piso, true).forEach(x -> porId.put(x.id(), x));
            Map<Integer, CatalogoRepository.Rotacion> rotPorId = new HashMap<>();
            catalogo.rotaciones(piso).forEach(r -> rotPorId.put(r.id(), r));
            List<Map<String, Object>> rots = new ArrayList<>();
            for (Map<String, Object> r : (List<Map<String, Object>>) py.get("rotaciones")) {
                Map<String, Object> x = new LinkedHashMap<>(r);
                var rot = rotPorId.get(((Number) r.get("id")).intValue());
                Cultivo c1 = rot != null ? porId.get(rot.cultivo1Id()) : null, c2 = rot != null ? porId.get(rot.cultivo2Id()) : null;
                if (c1 != null && c2 != null) {
                    x.put("usoAgua", aguaANivel(mayorAgua(c1.agua(), c2.agua())));
                    x.put("ciclo", ciclo(c1, c2, siembra, e.clim(), nivelLluvia, nivelNino, nivelHum));
                }
                rots.add(x);
            }
            out.put("rotaciones", rots);
            Map<String, Object> qh = new LinkedHashMap<>((Map<String, Object>) py.get("queHacer"));
            qh.put("tipo", tipoAccion((String) qh.get("accion")));
            out.put("queHacer", qh);
        }
        cache.put(clave, new Object[]{out, System.currentTimeMillis() + Duration.ofMinutes(30).toMillis()});
        return out;
    }

    // ------------------------------------------------------------------ perspectiva de la campaña
    private Map<String, Object> ciclo(Cultivo c1, Cultivo c2, YearMonth siembra, Climatologia clim, String nLluvia, String nNino, String nHum) {
        int m1 = Math.max(2, (int) Math.ceil((c1.cicloDias() == null ? 120 : c1.cicloDias()) / 30.0));
        int m2 = Math.max(2, (int) Math.ceil((c2.cicloDias() == null ? 120 : c2.cicloDias()) / 30.0));
        int dur = Math.min(m1 + Math.max(1, m2 / 2), 9);
        double[] lluvia = clim.get("PRECTOTCORR"), tmax = clim.get("T2M_MAX");
        double max = 0;
        for (double v : lluvia) max = Math.max(max, v * 30);
        List<Map<String, Object>> meses = new ArrayList<>();
        int peor = -1, peorNivel = -1;
        boolean nino = "alto".equals(nNino) || "alto".equals(nLluvia);
        for (int k = 0; k < dur; k++) {
            YearMonth ym = siembra.plusMonths(k);
            int m = ym.getMonthValue() - 1;
            Cultivo c = k < m1 ? c1 : c2;
            String riesgo = "bajo", motivo = "Condiciones normales para " + c.nombre().toLowerCase(), fuente = "NASA POWER";
            double lm = lluvia[m] * 30;
            if (k == 0 && "alto".equals(nHum) && !c.toleraSequia()) { riesgo = "alto"; motivo = "Suelo seco al sembrar"; }
            else if (k == 0 && "alto".equals(nLluvia) && !c.toleraInundacion()) { riesgo = "alto"; motivo = "Lluvia actual muy por encima de lo normal: riesgo de encharcamiento"; }
            else if (lm >= 0.6 * max && lm >= 25 && !c.toleraInundacion()) {
                riesgo = nino ? "alto" : "medio";
                motivo = "Temporada de lluvias, exceso de humedad" + (nino ? " y señal de El Niño" : "");
                if (nino) fuente = "NASA POWER + MUR SST";
            } else if (tmax[m] >= c.tempMax()) { riesgo = "medio"; motivo = String.format(Locale.ROOT, "Calor: la máxima normal es %.1f °C", tmax[m]); }
            Map<String, Object> mr = new LinkedHashMap<>();
            mr.put("mes", ym.toString());
            mr.put("riesgo", riesgo);
            mr.put("motivo", motivo);
            mr.put("fuente", fuente);
            meses.add(mr);
            int n = "alto".equals(riesgo) ? 2 : "medio".equals(riesgo) ? 1 : 0;
            if (n > peorNivel && n > 0) { peorNivel = n; peor = k; }
        }
        Map<String, Object> ciclo = new LinkedHashMap<>();
        ciclo.put("siembra", siembra.toString());
        ciclo.put("cosecha", siembra.plusMonths(dur - 1L).toString());
        ciclo.put("duracionMeses", dur);
        ciclo.put("meses", meses);
        if (peor >= 0) ciclo.put("mesMasRiesgoso", meses.get(peor).get("mes"));
        return ciclo;
    }

    // ------------------------------------------------------------------ cultivos permanentes
    private Map<String, Object> planPermanente(String nombre, String piso, Climatologia clim, String nLluvia, String nNino) {
        Integer id = catalogo.idCultivo(nombre);
        String cal = id == null ? null : catalogo.calendario(id, "costa".equals(piso) ? "costa" : piso);
        if (cal == null && id != null) cal = catalogo.calendario(id, "costa");
        if (cal == null) cal = "CCCCCCCCCCCC";
        Map<String, String> fases = catalogo.fases();
        double[] lluvia = clim.get("PRECTOTCORR");
        double max = 0;
        for (double v : lluvia) max = Math.max(max, v * 30);
        boolean nino = "alto".equals(nNino) || "alto".equals(nLluvia);
        YearMonth hoy = YearMonth.now();
        List<Map<String, Object>> meses = new ArrayList<>();
        for (int k = 0; k < 12; k++) {
            YearMonth ym = hoy.plusMonths(k);
            int m = ym.getMonthValue() - 1;
            String etapa = fases.getOrDefault(String.valueOf(cal.charAt(m)), "Crecimiento").toLowerCase();
            double lm = lluvia[m] * 30;
            String riesgo = "bajo", motivo = "Condiciones normales";
            if (lm >= 0.6 * max && lm >= 25) {
                riesgo = nino ? "alto" : "medio";
                motivo = "Temporada de lluvias" + (cal.charAt(m) == 'K' ? " durante la cosecha" : cal.charAt(m) == 'F' ? " durante la floración" : "") + (nino ? " y señal de El Niño" : "");
            }
            Map<String, Object> mr = new LinkedHashMap<>();
            mr.put("mes", ym.toString());
            mr.put("riesgo", riesgo);
            mr.put("motivo", motivo);
            mr.put("fuente", nino ? "NASA POWER + MUR SST" : "NASA POWER");
            mr.put("etapa", etapa);
            meses.add(mr);
        }
        List<Map<String, Object>> acciones = new ArrayList<>();
        if (id != null) {
            for (var a : catalogo.acciones(id)) {
                acciones.add(Map.of("etapa", fases.getOrDefault(a.fase(), a.fase()).toLowerCase(), "accion", a.descripcion(),
                        "motivo", a.alerta() == null ? "" : a.alerta(), "fuente", "NASA POWER"));
            }
        }
        Map<String, Object> plan = new LinkedHashMap<>();
        plan.put("cultivo", nombre);
        plan.put("etapaActual", meses.get(0).get("etapa"));
        plan.put("meses", meses);
        plan.put("acciones", acciones);
        return plan;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> queHacerPermanente(String nombre, Map<String, Object> plan, Map<String, Object> ind, String nLluvia, String nNino, String nHum) {
        String etapa = (String) plan.get("etapaActual");
        Map<String, Object> q = new LinkedHashMap<>();
        if ("alto".equals(nLluvia) || "alto".equals(nNino)) {
            q.put("tipo", "preparar drenaje");
            q.put("accion", "Prepara drenajes y protege tu " + nombre.toLowerCase() + " (" + etapa + ")");
            q.put("motivo", detalleDe(ind, "alto".equals(nNino) ? "elNino" : "lluvia"));
            q.put("fuente", "alto".equals(nNino) ? "MUR SST" : "NASA POWER");
        } else if ("alto".equals(nHum)) {
            q.put("tipo", "regar");
            q.put("accion", "Refuerza el riego de tu " + nombre.toLowerCase() + ": el suelo está seco");
            q.put("motivo", detalleDe(ind, "humedadSuelo"));
            q.put("fuente", "NASA POWER");
        } else {
            List<Map<String, Object>> acc = (List<Map<String, Object>>) plan.get("acciones");
            String texto = acc.stream().filter(a -> etapa.equals(a.get("etapa"))).map(a -> (String) a.get("accion")).findFirst()
                    .orElse("Mantén el riego y la sanidad del cultivo");
            q.put("tipo", "regar");
            q.put("accion", texto);
            q.put("motivo", "Tu " + nombre.toLowerCase() + " está en " + etapa + " y el clima está dentro de lo normal");
            q.put("fuente", "NASA POWER");
        }
        return q;
    }

    // ------------------------------------------------------------------ utilidades
    @SuppressWarnings("unchecked")
    private static String nivel(Map<String, Object> ind, String k) {
        Object v = ind.get(k);
        return v == null ? null : (String) ((Map<String, Object>) v).get("nivel");
    }

    @SuppressWarnings("unchecked")
    private static String detalleDe(Map<String, Object> ind, String k) {
        Object v = ind.get(k);
        return v == null ? "" : String.valueOf(((Map<String, Object>) v).getOrDefault("detalle", ""));
    }

    /** Texto simple con el número que decide (campo opcional "detalle" del contrato de la app). */
    private static void detalle(String k, Map<String, Object> i) {
        double valor = ((Number) i.get("valor")).doubleValue(), normal = ((Number) i.get("normal")).doubleValue();
        String t = switch (k) {
            case "lluvia" -> normal < 3
                    ? String.format(Locale.ROOT, "Lluvia de %.1f mm/día frente a %.1f mm/día normales (%.0f mm en 30 días)", valor, normal, valor * 30)
                    : String.format(Locale.ROOT, "Lluvia %.0f %% %s de lo normal", Math.abs(valor / normal - 1) * 100, valor < normal ? "por debajo" : "por encima");
            case "humedadSuelo" -> String.format(Locale.ROOT, "Humedad del suelo %.0f %% %s de lo normal", Math.abs(valor / Math.max(normal, 0.01) - 1) * 100, valor < normal ? "por debajo" : "por encima");
            case "calor" -> String.format(Locale.ROOT, "Máxima de %.1f °C frente a %.1f °C normales", valor, normal);
            default -> String.format(Locale.ROOT, "Mar %.1f °C %s de lo normal frente a la costa", Math.abs(valor), valor >= 0 ? "más caliente" : "más frío");
        };
        i.put("detalle", t);
    }

    private static String tipoAccion(String accion) {
        String a = accion == null ? "" : accion.toLowerCase();
        if (a.contains("drena")) return "preparar drenaje";
        if (a.contains("esper") || a.contains("no siembres") || a.contains("todavía no")) return "esperar";
        if (a.contains("proteg")) return "proteger";
        if (a.contains("reg")) return "regar";
        return "sembrar";
    }

    private static String mayorAgua(String a, String b) {
        List<String> orden = List.of("baja", "media", "alta");
        return orden.indexOf(a) >= orden.indexOf(b) ? a : b;
    }

    private static String aguaANivel(String a) {
        return switch (a) { case "baja" -> "bajo"; case "alta" -> "alto"; default -> "medio"; };
    }

    public static String mesNombre(int m0) { return MES_NOMBRE[m0]; }

    private static double r1(double x) { return Math.round(x * 10) / 10.0; }
    private static double r2(double x) { return Math.round(x * 100) / 100.0; }
    private static double r3(double x) { return Math.round(x * 1000) / 1000.0; }
}
