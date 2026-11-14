package pe.halcondorado.allpashift.asistente;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * Cliente de Groq (API compatible con OpenAI): POST https://api.groq.com/openai/v1/chat/completions.
 * Modelo en GROQ_MODEL (por defecto openai/gpt-oss-20b, licencia Apache 2.0). La clave SOLO en GROQ_API_KEY.
 * Sin clave, el asistente responde solo en modo "respaldo".
 */
@Service
public class GroqClient {

    private static final Logger log = LoggerFactory.getLogger(GroqClient.class);
    static final double TEMPERATURA = 0.2;
    static final int MAX_TOKENS = 300;

    private final String apiKey;
    private final String modelo;
    private final RestClient groq;

    public GroqClient(@Value("${GROQ_API_KEY:}") String apiKey,
                      @Value("${GROQ_MODEL:openai/gpt-oss-20b}") String modelo,
                      @Value("${GROQ_URL:https://api.groq.com/openai/v1}") String url,
                      @Value("${GROQ_TIMEOUT_SEGUNDOS:8}") int timeoutSegundos) {
        this.apiKey = apiKey;
        this.modelo = modelo;
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
        Map<String, Object> cuerpo = Map.of(
                "model", modelo,
                "temperature", TEMPERATURA,
                "max_tokens", MAX_TOKENS,
                "messages", List.of(
                        Map.of("role", "system", "content", sistema),
                        Map.of("role", "user", "content", usuario)));
        try {
            Map<String, Object> r = groq.post().uri("/chat/completions")
                    .header("Authorization", "Bearer " + apiKey)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(cuerpo).retrieve().body(Map.class);
            List<Map<String, Object>> choices = r == null ? null : (List<Map<String, Object>>) r.get("choices");
            if (choices == null || choices.isEmpty()) throw new GroqException("respuesta_sin_texto");
            Object texto = ((Map<String, Object>) choices.get(0).get("message")).get("content");
            if (texto == null) throw new GroqException("respuesta_sin_texto");
            return texto.toString();
        } catch (RestClientException e) {
            throw new GroqException("groq_error_" + e.getClass().getSimpleName());
        }
    }

    public static class GroqException extends RuntimeException {
        public GroqException(String motivo) {
            super(motivo);
        }
    }
}
