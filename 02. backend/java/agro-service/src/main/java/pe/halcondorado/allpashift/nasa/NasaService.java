package pe.halcondorado.allpashift.nasa;

import java.time.Duration;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

/**
 * Datos de la NASA que la API Java descarga y luego entrega a climate-service (contrato del backend).
 * - NASA POWER: normal climatológica, últimos 30 días y series mensuales (sin login).
 * - MUR SST (NASA JPL) vía ERDDAP de NOAA: anomalía de la temperatura del mar (El Niño costero).
 * Todo se guarda en memoria unas horas para no repetir descargas.
 */
@Service
public class NasaService {

    private static final Logger log = LoggerFactory.getLogger(NasaService.class);
    private static final String POWER = "https://power.larc.nasa.gov/api/temporal";
    private static final String ERDDAP = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41anom1day.json";
    private static final String[] MESES = {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"};
    private static final DateTimeFormatter AMD = DateTimeFormatter.BASIC_ISO_DATE;

    private final RestClient http;
    private final Map<String, Object[]> cache = new ConcurrentHashMap<>();

    public NasaService() {
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        f.setConnectTimeout(Duration.ofSeconds(10));
        f.setReadTimeout(Duration.ofSeconds(40));
        this.http = RestClient.builder().requestFactory(f).defaultHeader("User-Agent", "AllpaShift/1.0 (NASA Space Apps 2026)").build();
    }

    /** Normal de cada mes (12 valores) por parámetro: PRECTOTCORR (mm/día), GWETTOP, GWETROOT, T2M_MAX, T2M_MIN, T2M. */
    public record Climatologia(Map<String, double[]> param) {
        public double[] get(String p) { return param.get(p); }
    }

    /** Promedio de los últimos 30 días con dato. */
    public record Reciente(double lluviaMmDia, double humedadSup, double tMax, double tMin, String ultimoDia, int dias) {}

    public Climatologia climatologia(double lat, double lon) {
        return enCache("clim:" + k(lat, lon), Duration.ofHours(24), () -> {
            Map<?, ?> j = http.get().uri(POWER + "/climatology/point?parameters=PRECTOTCORR,GWETTOP,GWETROOT,T2M_MAX,T2M_MIN,T2M&community=AG&longitude={lon}&latitude={lat}&format=JSON", lon, lat)
                    .retrieve().body(Map.class);
            Map<String, double[]> out = new HashMap<>();
            parametros(j).forEach((nombre, valores) -> {
                double[] v = new double[12];
                for (int m = 0; m < 12; m++) v[m] = num(((Map<?, ?>) valores).get(MESES[m]));
                out.put((String) nombre, v);
            });
            return new Climatologia(out);
        });
    }

    public Reciente reciente(double lat, double lon) {
        return enCache("rec:" + k(lat, lon), Duration.ofHours(3), () -> {
            LocalDate hoy = LocalDate.now();
            Map<?, ?> j = http.get().uri(POWER + "/daily/point?parameters=PRECTOTCORR,GWETTOP,T2M_MAX,T2M_MIN&community=AG&longitude={lon}&latitude={lat}&start={ini}&end={fin}&format=JSON",
                    lon, lat, hoy.minusDays(45).format(AMD), hoy.format(AMD)).retrieve().body(Map.class);
            Map<?, ?> p = parametros(j);
            Map<?, ?> lluvia = (Map<?, ?>) p.get("PRECTOTCORR"), hum = (Map<?, ?>) p.get("GWETTOP"),
                    tmax = (Map<?, ?>) p.get("T2M_MAX"), tmin = (Map<?, ?>) p.get("T2M_MIN");
            List<String> dias = new ArrayList<>();
            for (Object d : lluvia.keySet()) {
                if (num(lluvia.get(d)) != -999 && num(hum.get(d)) != -999 && num(tmax.get(d)) != -999) dias.add((String) d);
            }
            dias.sort(null);
            if (dias.size() > 30) dias = dias.subList(dias.size() - 30, dias.size());
            if (dias.size() < 10) return null;
            double l = 0, h = 0, tx = 0, tn = 0;
            for (String d : dias) { l += num(lluvia.get(d)); h += num(hum.get(d)); tx += num(tmax.get(d)); tn += num(tmin.get(d)); }
            int n = dias.size();
            return new Reciente(l / n, h / n, tx / n, tn / n, dias.get(n - 1), n);
        });
    }

    /** Anomalía de la temperatura del mar (°C) a ~1° mar adentro; null fuera de la costa del Pacífico o si no responde. */
    public Double sstAnomalia(double lat, double lon) {
        if (lon > -78 || lat < -20 || lat > 5) return null;
        double la = Math.max(-18, Math.min(2, lat));
        double lo = Math.min(lon - 0.9, -81.2);
        try {
            return enCache("sst:" + k(la, lo), Duration.ofHours(6), () -> {
                String url = ERDDAP + "?sstAnom%5B(last)%5D%5B(" + fmt(la) + ")%5D%5B(" + fmt(lo) + ")%5D";
                Map<?, ?> j = http.get().uri(java.net.URI.create(url)).retrieve().body(Map.class);
                List<?> fila = (List<?>) ((List<?>) ((Map<?, ?>) j.get("table")).get("rows")).get(0);
                Object v = fila.get(3);
                return v == null ? null : num(v);
            });
        } catch (Exception e) {
            log.warn("MUR SST no disponible: {}", e.getMessage());
            return null;
        }
    }

    /** Serie mensual de un año: PRECTOTCORR (mm/día) y GWETROOT por mes (12 valores; NaN = sin dato). */
    public Map<String, double[]> mensual(double lat, double lon, int anio) {
        return enCache("men:" + k(lat, lon) + ":" + anio, Duration.ofHours(24), () -> {
            Map<?, ?> j = http.get().uri(POWER + "/monthly/point?parameters=PRECTOTCORR,GWETROOT&community=AG&longitude={lon}&latitude={lat}&start={a}&end={a}&format=JSON", lon, lat, anio, anio)
                    .retrieve().body(Map.class);
            Map<String, double[]> out = new HashMap<>();
            parametros(j).forEach((nombre, valores) -> {
                double[] v = new double[12];
                for (int m = 0; m < 12; m++) {
                    double x = num(((Map<?, ?>) valores).get(String.format("%d%02d", anio, m + 1)));
                    v[m] = x == -999 ? Double.NaN : x;
                }
                out.put((String) nombre, v);
            });
            return out;
        });
    }

    // ------------------------------------------------------------------ utilidades
    @SuppressWarnings("unchecked")
    private <T> T enCache(String clave, Duration ttl, Supplier<T> carga) {
        Object[] e = cache.get(clave);
        long ahora = System.currentTimeMillis();
        if (e != null && (long) e[1] > ahora) return (T) e[0];
        T v = carga.get();
        if (v != null) cache.put(clave, new Object[]{v, ahora + ttl.toMillis()});
        return v;
    }

    private static Map<?, ?> parametros(Map<?, ?> j) {
        return (Map<?, ?>) ((Map<?, ?>) j.get("properties")).get("parameter");
    }

    private static double num(Object o) {
        return o instanceof Number n ? n.doubleValue() : -999;
    }

    private static String k(double lat, double lon) {
        return fmt(lat) + "," + fmt(lon);
    }

    private static String fmt(double x) {
        return String.format(Locale.ROOT, "%.2f", x);
    }
}
