package pe.halcondorado.allpashift.calculos;

import java.time.Duration;
import java.util.Map;
import java.util.function.Supplier;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * Cliente del servicio de cálculos en Python ('02. backend/python/calculos', puerto 8001).
 * Regla 3 (doc 29): Python descarga de la NASA y calcula; Java solo lo llama y graba el resultado.
 * Responde ya con la forma del contrato del frontend (types/api.ts).
 */
@Service
public class CalculosClient {

    private final RestClient calculos;

    public CalculosClient(@Value("${CALCULOS_URL:http://localhost:8001}") String url) {
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        f.setConnectTimeout(Duration.ofSeconds(5));
        f.setReadTimeout(Duration.ofSeconds(60));   // la primera consulta de un punto descarga NASA POWER (~3-10 s)
        this.calculos = RestClient.builder().baseUrl(url).requestFactory(f).build();
    }

    /** POST /calcular {lat, lon, lang, tipoCultivo, mesSiembra | cultivo, catalogo} → recomendación completa. */
    public Map<String, Object> calcular(Map<String, Object> pedido) {
        return llamar(() -> calculos.post().uri("/calcular").contentType(MediaType.APPLICATION_JSON).body(pedido).retrieve().body(Map.class));
    }

    /** POST /indicadores-punto {lat, lon, lang} → {nivel, indicadorDecisivo, indicadores}. */
    public Map<String, Object> indicadoresPunto(double lat, double lon, String lang) {
        return llamar(() -> calculos.post().uri("/indicadores-punto").contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("lat", lat, "lon", lon, "lang", lang)).retrieve().body(Map.class));
    }

    /** GET /validacion?anio=&lat=&lon=&lang= → lluvia GPM IMERG, alerta MUR SST, semanas de anticipación. */
    public Map<String, Object> validacion(int anio, double lat, double lon, String lang) {
        return llamar(() -> calculos.get().uri(u -> u.path("/validacion").queryParam("anio", anio).queryParam("lat", lat)
                .queryParam("lon", lon).queryParam("lang", lang).build()).retrieve().body(Map.class));
    }

    /** GET /validacion/detalle?anio=&mes=&lat=&lon= → lluvia del mes día por día y por semana (IMERG diario). */
    public Map<String, Object> detalleLluvia(int anio, int mes, double lat, double lon) {
        try {
            return llamar(() -> calculos.get().uri(u -> u.path("/validacion/detalle").queryParam("anio", anio).queryParam("mes", mes)
                    .queryParam("lat", lat).queryParam("lon", lon).build()).retrieve().body(Map.class));
        } catch (CalculosNoDisponibleException e) {
            if (e.getCause() instanceof org.springframework.web.client.HttpClientErrorException.NotFound) {
                return Map.of("anio", anio, "mes", mes, "sinDato", true);   // no hay lluvia diaria para ese mes/lugar
            }
            throw e;
        }
    }

    /** GET /validacion/anios?lat=&lon= → años con datos reales. */
    public Map<String, Object> anios(double lat, double lon) {
        return llamar(() -> calculos.get().uri(u -> u.path("/validacion/anios").queryParam("lat", lat).queryParam("lon", lon).build())
                .retrieve().body(Map.class));
    }

    /** GET /salud */
    public Map<String, Object> salud() {
        return llamar(() -> calculos.get().uri("/salud").retrieve().body(Map.class));
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> llamar(Supplier<Map> llamada) {
        try {
            Map<String, Object> r = llamada.get();
            if (r == null) throw new CalculosNoDisponibleException("Respuesta vacía del servicio de cálculos", null);
            return r;
        } catch (RestClientException e) {
            throw new CalculosNoDisponibleException(e.getMessage(), e);
        }
    }

    /** El servicio de cálculos no respondió (caído, timeout o error HTTP). */
    public static class CalculosNoDisponibleException extends RuntimeException {
        public CalculosNoDisponibleException(String mensaje, Throwable causa) {
            super(mensaje, causa);
        }
    }
}
