package pe.halcondorado.allpashift.asistente;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

import pe.halcondorado.allpashift.api.ErroresApi.ApiError;

/** Máximo 10 preguntas por minuto por IP (ventana deslizante en memoria). */
@Component
public class LimitadorPreguntas {

    static final int MAXIMO = 10;
    static final long VENTANA_MS = 60_000;

    private final Map<String, Deque<Long>> porIp = new ConcurrentHashMap<>();

    /** Registra una pregunta de esta IP o lanza 429 {"error": "demasiadas_preguntas"}. */
    public void registrar(String ip) {
        long ahora = System.currentTimeMillis();
        Deque<Long> tiempos = porIp.computeIfAbsent(ip, k -> new ArrayDeque<>());
        synchronized (tiempos) {
            while (!tiempos.isEmpty() && ahora - tiempos.peekFirst() >= VENTANA_MS) tiempos.pollFirst();
            if (tiempos.size() >= MAXIMO) {
                throw new ApiError(HttpStatus.TOO_MANY_REQUESTS, "demasiadas_preguntas",
                        "Máximo " + MAXIMO + " preguntas por minuto. Espera un momento.");
            }
            tiempos.addLast(ahora);
        }
    }
}
