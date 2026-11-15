package pe.halcondorado.allpashift.asistente;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;
import java.util.Map;
import java.util.function.LongSupplier;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * Cliente de Groq (API compatible con OpenAI): POST https://api.groq.com/openai/v1/chat/completions.
 * Modelo en GROQ_MODEL (por defecto openai/gpt-oss-20b, licencia Apache 2.0). La clave SOLO en GROQ_API_KEY.
 * Sin clave, el asistente responde solo en modo "respaldo".
 *
 * <p>Plan gratuito de Groq para gpt-oss-20b (docs de Groq, 14-nov-2026): 30 solicitudes/min, 1 000 al día, 8 000 tokens/min y
 * 200 000 tokens al día POR CLAVE (no por IP). Cada pregunta gasta ~2 000-3 000 tokens, así que el tope real es ~3 preguntas
 * por minuto y ~70-80 al día. {@link Cupo} lleva la cuenta (con un margen) y evita llamar a Groq cuando ya no hay cupo:
 * el asistente pasa a "respaldo" sin esperar un 429. Si Groq igual responde 429, se respeta su cabecera Retry-After.
 */
@Service
public class GroqClient {

    private static final Logger log = LoggerFactory.getLogger(GroqClient.class);
    static final double TEMPERATURA = 0.2;
    static final int MAX_TOKENS = 1024;  // gpt-oss razona antes de responder: con pocos tokens devolvía texto vacío
    /** Estimación de lo que gasta la respuesta (razonamiento corto + texto), para reservar cupo antes de llamar. */
    static final int TOKENS_RESPUESTA_ESTIMADOS = 450;

    private final String apiKey;
    private final String modelo;
    private final RestClient groq;
    private final Cupo cupo;

    @Autowired
    public GroqClient(@Value("${GROQ_API_KEY:}") String apiKey,
                      @Value("${GROQ_MODEL:openai/gpt-oss-20b}") String modelo,
                      @Value("${GROQ_URL:https://api.groq.com/openai/v1}") String url,
                      @Value("${GROQ_TIMEOUT_SEGUNDOS:8}") int timeoutSegundos,
                      @Value("${GROQ_TPM:6800}") int tokensPorMinuto,
                      @Value("${GROQ_TPD:180000}") int tokensPorDia,
                      @Value("${GROQ_RPM:25}") int solicitudesPorMinuto,
                      @Value("${GROQ_RPD:900}") int solicitudesPorDia) {
        this(apiKey, modelo, url, timeoutSegundos,
                new Cupo(tokensPorMinuto, tokensPorDia, solicitudesPorMinuto, solicitudesPorDia, System::currentTimeMillis));
    }

    /** Para las pruebas: con su propio cupo (y reloj). */
    GroqClient(String apiKey, String modelo, String url, int timeoutSegundos, Cupo cupo) {
        this.apiKey = apiKey;
        this.modelo = modelo;
        this.cupo = cupo;
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        f.setConnectTimeout(Duration.ofSeconds(3));
        f.setReadTimeout(Duration.ofSeconds(timeoutSegundos));
        this.groq = RestClient.builder().baseUrl(url).requestFactory(f).build();
    }

    public boolean habilitado() {
        return apiKey != null && !apiKey.isBlank();
    }

    public String modelo() {
        return modelo;
    }

    /** Al arrancar, deja dicho en el log en qué modo funciona el asistente (sin mostrar la clave). */
    @EventListener(ApplicationReadyEvent.class)
    void avisarModo() {
        if (habilitado()) log.info("Asistente: modo IA con Groq, modelo {}", modelo);
        else log.warn("Asistente: GROQ_API_KEY no configurada; responde solo en modo respaldo (queHacer)");
    }

    /** Texto de la respuesta del modelo. Lanza GroqException ante cualquier fallo (nunca con la clave en el mensaje). */
    @SuppressWarnings("unchecked")
    public String chat(String sistema, String usuario) {
        int estimado = (sistema.length() + usuario.length()) / 3 + TOKENS_RESPUESTA_ESTIMADOS;
        cupo.reservar(estimado);   // GroqException("cupo_groq_...") si ya no hay cupo: no se llama a Groq
        Map<String, Object> cuerpo = Map.of(
                "model", modelo,
                "temperature", TEMPERATURA,
                "max_tokens", MAX_TOKENS,
                "reasoning_effort", "low",       // razonamiento corto: respuesta rápida y con texto
                "include_reasoning", false,      // solo la respuesta final
                "messages", List.of(
                        Map.of("role", "system", "content", sistema),
                        Map.of("role", "user", "content", usuario)));
        try {
            Map<String, Object> r = groq.post().uri("/chat/completions")
                    .header("Authorization", "Bearer " + apiKey)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(cuerpo).retrieve().body(Map.class);
            if (r != null && r.get("usage") instanceof Map<?, ?> uso && uso.get("total_tokens") instanceof Number total) {
                cupo.ajustar(estimado, total.intValue());   // lo que Groq realmente cobró
            }
            List<Map<String, Object>> choices = r == null ? null : (List<Map<String, Object>>) r.get("choices");
            if (choices == null || choices.isEmpty()) throw new GroqException("respuesta_sin_texto");
            Object texto = ((Map<String, Object>) choices.get(0).get("message")).get("content");
            if (texto == null) throw new GroqException("respuesta_sin_texto");
            return texto.toString();
        } catch (HttpClientErrorException.TooManyRequests e) {
            long espera = cupo.enfriar(e.getResponseHeaders() == null ? null : e.getResponseHeaders().getFirst("retry-after"));
            log.warn("Groq respondió 429: sin llamar a Groq durante {} s", espera);
            throw new GroqException("groq_429_espera_" + espera + "s");
        } catch (RestClientException e) {
            throw new GroqException("groq_error_" + e.getClass().getSimpleName());
        }
    }

    public static class GroqException extends RuntimeException {
        public GroqException(String motivo) {
            super(motivo);
        }
    }

    /**
     * Cuenta del cupo gratuito (ventana deslizante de 1 minuto y tope por día UTC) y enfriamiento tras un 429.
     * Los topes por defecto son el 85-90 % del plan gratuito para no chocar con el límite real.
     */
    static final class Cupo {
        static final long MIN_ESPERA_S = 5, MAX_ESPERA_S = 3600, ESPERA_POR_DEFECTO_S = 30;

        private final int tpm, tpd, rpm, rpd;
        private final LongSupplier reloj;
        private final Deque<long[]> ultimoMinuto = new ArrayDeque<>();   // {instante en ms, tokens}
        private LocalDate dia;
        private int tokensDia, solicitudesDia;
        private long enfriarHastaMs;

        Cupo(int tpm, int tpd, int rpm, int rpd, LongSupplier reloj) {
            this.tpm = tpm;
            this.tpd = tpd;
            this.rpm = rpm;
            this.rpd = rpd;
            this.reloj = reloj;
        }

        /** Reserva cupo para una llamada o lanza GroqException con el motivo (sin llamar a Groq). */
        synchronized void reservar(int tokensEstimados) {
            long ahora = reloj.getAsLong();
            limpiar(ahora);
            if (ahora < enfriarHastaMs) throw new GroqException("cupo_groq_espera_" + (enfriarHastaMs - ahora + 999) / 1000 + "s");
            if (solicitudesDia >= rpd) throw new GroqException("cupo_groq_solicitudes_por_dia");
            if (tokensDia + tokensEstimados > tpd) throw new GroqException("cupo_groq_tokens_por_dia");
            if (ultimoMinuto.size() >= rpm) throw new GroqException("cupo_groq_solicitudes_por_minuto");
            int enMinuto = ultimoMinuto.stream().mapToInt(x -> (int) x[1]).sum();
            if (enMinuto + tokensEstimados > tpm) throw new GroqException("cupo_groq_tokens_por_minuto");
            ultimoMinuto.addLast(new long[] {ahora, tokensEstimados});
            tokensDia += tokensEstimados;
            solicitudesDia++;
        }

        /** Cambia lo estimado por lo que Groq realmente cobró. */
        synchronized void ajustar(int estimados, int reales) {
            long[] ultima = ultimoMinuto.peekLast();
            if (ultima != null) ultima[1] += reales - estimados;
            tokensDia += reales - estimados;
        }

        /** Tras un 429: no se llama a Groq hasta que pase Retry-After (en segundos, entre 5 y 3 600). Devuelve la espera. */
        synchronized long enfriar(String retryAfter) {
            long espera = ESPERA_POR_DEFECTO_S;
            try {
                if (retryAfter != null && !retryAfter.isBlank()) espera = (long) Math.ceil(Double.parseDouble(retryAfter.trim()));
            } catch (NumberFormatException ignorado) {
                // cabecera rara: se usa el valor por defecto
            }
            espera = Math.max(MIN_ESPERA_S, Math.min(MAX_ESPERA_S, espera));
            enfriarHastaMs = reloj.getAsLong() + espera * 1000;
            return espera;
        }

        private void limpiar(long ahora) {
            while (!ultimoMinuto.isEmpty() && ahora - ultimoMinuto.peekFirst()[0] >= 60_000) ultimoMinuto.pollFirst();
            LocalDate hoy = Instant.ofEpochMilli(ahora).atZone(ZoneOffset.UTC).toLocalDate();
            if (!hoy.equals(dia)) {
                dia = hoy;
                tokensDia = 0;
                solicitudesDia = 0;
            }
        }
    }
}
