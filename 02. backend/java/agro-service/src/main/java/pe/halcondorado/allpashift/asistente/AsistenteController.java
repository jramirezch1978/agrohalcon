package pe.halcondorado.allpashift.asistente;

import java.util.LinkedHashMap;
import java.util.Map;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import pe.halcondorado.allpashift.calculos.CalculosClient;

@RestController
@RequestMapping("/api")
public class AsistenteController {

    private final AsistenteService asistente;
    private final LimitadorPreguntas limitador;
    private final CalculosClient calculos;

    public AsistenteController(AsistenteService asistente, LimitadorPreguntas limitador, CalculosClient calculos) {
        this.asistente = asistente;
        this.limitador = limitador;
        this.calculos = calculos;
    }

    /** Explica la recomendación ya calculada (IA con Groq o respaldo). Máx. 10 preguntas por minuto por IP. */
    @PostMapping("/asistente")
    public AsistenteRespuesta preguntar(@Valid @RequestBody AsistenteRequest pregunta, HttpServletRequest http) {
        limitador.registrar(ip(http));
        return asistente.responder(pregunta);
    }

    /** Estado: servicio de cálculos y modo del asistente ("ia" | "solo_respaldo"). */
    @GetMapping("/salud")
    public Map<String, Object> salud() {
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("api", "ok");
        String estadoCalculos;
        try {
            calculos.salud();
            estadoCalculos = "ok";
        } catch (CalculosClient.CalculosNoDisponibleException e) {
            estadoCalculos = "no_disponible";
        }
        r.put("calculos", estadoCalculos);
        r.put("asistente", asistente.modo());
        return r;
    }

    /**
     * IP real del cliente para el límite de preguntas. Se usa X-Real-IP, que nginx SOBRESCRIBE con $remote_addr
     * (el cliente no lo puede falsificar). Nunca el primer valor de X-Forwarded-For: ese lo escribe el propio cliente
     * y bastaría cambiarlo en cada pregunta para saltarse el límite. Sin nginx (desarrollo): la IP de la conexión.
     */
    static String ip(HttpServletRequest http) {
        String real = http.getHeader("X-Real-IP");
        return real != null && !real.isBlank() ? real.trim() : http.getRemoteAddr();
    }
}
