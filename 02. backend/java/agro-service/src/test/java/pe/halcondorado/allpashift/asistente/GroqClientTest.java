package pe.halcondorado.allpashift.asistente;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import com.sun.net.httpserver.HttpServer;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import pe.halcondorado.allpashift.asistente.GroqClient.Cupo;
import pe.halcondorado.allpashift.asistente.GroqClient.GroqException;

/** Cupo gratuito de Groq (30 solicitudes/min, 1 000/día, 8 000 tokens/min, 200 000/día) y 429, con un Groq falso en un puerto local. */
class GroqClientTest {

    static final String CLAVE = "CLAVE-FALSA-DE-PRUEBA-que-nunca-debe-aparecer-123456";

    HttpServer servidor;
    AtomicInteger llamadas;
    AtomicInteger estado;          // código HTTP que responde el Groq falso
    volatile String retryAfter;    // cabecera Retry-After en los 429
    volatile int tokensCobrados;   // usage.total_tokens de las respuestas 200
    AtomicLong reloj;

    @BeforeEach
    void arrancarGroqFalso() throws IOException {
        llamadas = new AtomicInteger();
        estado = new AtomicInteger(200);
        retryAfter = null;
        tokensCobrados = 1500;
        reloj = new AtomicLong(1_700_000_000_000L);
        servidor = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        servidor.createContext("/chat/completions", ex -> {
            llamadas.incrementAndGet();
            ex.getRequestBody().readAllBytes();
            String cuerpo = estado.get() == 200
                    ? "{\"choices\":[{\"message\":{\"content\":\"respuesta de prueba\"}}],\"usage\":{\"total_tokens\":" + tokensCobrados + "}}"
                    : "{\"error\":{\"message\":\"rate limit " + CLAVE + "\"}}";
            if (retryAfter != null && estado.get() == 429) ex.getResponseHeaders().add("retry-after", retryAfter);
            ex.getResponseHeaders().add("Content-Type", "application/json");
            byte[] b = cuerpo.getBytes(StandardCharsets.UTF_8);
            ex.sendResponseHeaders(estado.get(), b.length);
            ex.getResponseBody().write(b);
            ex.close();
        });
        servidor.start();
    }

    @AfterEach
    void apagar() {
        servidor.stop(0);
    }

    GroqClient cliente(int tpm, int tpd, int rpm, int rpd) {
        String url = "http://127.0.0.1:" + servidor.getAddress().getPort();
        return new GroqClient(CLAVE, "openai/gpt-oss-20b", url, 5, new Cupo(tpm, tpd, rpm, rpd, reloj::get));
    }

    @Test
    void unaLlamadaNormalDevuelveElTexto() {
        assertThat(cliente(6800, 180000, 25, 900).chat("sistema", "usuario")).isEqualTo("respuesta de prueba");
        assertThat(llamadas.get()).isEqualTo(1);
    }

    @Test
    void cuandoSeAcabanLosTokensPorMinutoYaNoLlamaAGroqHastaQuePaseElMinuto() {
        GroqClient c = cliente(3300, 180000, 25, 900);   // cada respuesta cobra 1 500 y reservar pide ~450: caben 2 por minuto
        c.chat("s", "u");
        c.chat("s", "u");
        assertThatThrownBy(() -> c.chat("s", "u")).isInstanceOf(GroqException.class).hasMessage("cupo_groq_tokens_por_minuto");
        assertThat(llamadas.get()).isEqualTo(2);        // la tercera NO salió hacia Groq
        reloj.addAndGet(61_000);
        assertThat(c.chat("s", "u")).isEqualTo("respuesta de prueba");
        assertThat(llamadas.get()).isEqualTo(3);
    }

    @Test
    void usaLosTokensRealesQueCobraGroqNoLaEstimacion() {
        tokensCobrados = 100;                           // respuestas baratas: con solo la estimación (~450 c/u) cabrían 3; con lo real, 8 o más
        GroqClient c = cliente(1500, 180000, 25, 900);
        for (int i = 0; i < 8; i++) c.chat("s", "u");
        assertThat(llamadas.get()).isEqualTo(8);
    }

    @Test
    void haySolicitudesPorMinutoPorDiaYTokensPorDia() {
        GroqClient porMinuto = cliente(100000, 180000, 2, 900);
        porMinuto.chat("s", "u");
        porMinuto.chat("s", "u");
        assertThatThrownBy(() -> porMinuto.chat("s", "u")).hasMessage("cupo_groq_solicitudes_por_minuto");

        GroqClient porDia = cliente(100000, 180000, 25, 2);
        porDia.chat("s", "u");
        reloj.addAndGet(61_000);
        porDia.chat("s", "u");
        reloj.addAndGet(61_000);
        assertThatThrownBy(() -> porDia.chat("s", "u")).hasMessage("cupo_groq_solicitudes_por_dia");

        GroqClient tokensDia = cliente(100000, 1900, 25, 900);   // 1 500 ya gastados + ~450 de la siguiente pasan de 1 900
        tokensDia.chat("s", "u");
        reloj.addAndGet(61_000);
        assertThatThrownBy(() -> tokensDia.chat("s", "u")).hasMessage("cupo_groq_tokens_por_dia");
        reloj.addAndGet(24L * 3600 * 1000);              // otro día UTC: se reinicia
        assertThat(tokensDia.chat("s", "u")).isEqualTo("respuesta de prueba");
    }

    @Test
    void unTooManyRequestsRespetaRetryAfterYNoVuelveALlamarAntes() {
        estado.set(429);
        retryAfter = "7";
        GroqClient c = cliente(6800, 180000, 25, 900);
        assertThatThrownBy(() -> c.chat("s", "u")).isInstanceOf(GroqException.class).hasMessage("groq_429_espera_7s");
        estado.set(200);
        assertThatThrownBy(() -> c.chat("s", "u")).hasMessageStartingWith("cupo_groq_espera_");   // en enfriamiento: sin llamar
        assertThat(llamadas.get()).isEqualTo(1);
        reloj.addAndGet(7_001);
        assertThat(c.chat("s", "u")).isEqualTo("respuesta de prueba");
        assertThat(llamadas.get()).isEqualTo(2);
    }

    @Test
    void retryAfterRaroOEnormeSeAcota() {
        Cupo cupo = new Cupo(6800, 180000, 25, 900, reloj::get);
        assertThat(cupo.enfriar(null)).isEqualTo(Cupo.ESPERA_POR_DEFECTO_S);
        assertThat(cupo.enfriar("no-es-un-numero")).isEqualTo(Cupo.ESPERA_POR_DEFECTO_S);
        assertThat(cupo.enfriar("1")).isEqualTo(Cupo.MIN_ESPERA_S);
        assertThat(cupo.enfriar("99999")).isEqualTo(Cupo.MAX_ESPERA_S);
        assertThat(cupo.enfriar("2.5")).isEqualTo(Cupo.MIN_ESPERA_S);
    }

    @Test
    void laClaveNuncaApareceEnLosMensajesDeError() {
        estado.set(401);
        GroqClient c = cliente(6800, 180000, 25, 900);
        assertThatThrownBy(() -> c.chat("s", "u")).isInstanceOf(GroqException.class)
                .satisfies(e -> assertThat(e.getMessage()).doesNotContain(CLAVE).startsWith("groq_error_"));
        estado.set(429);
        GroqClient d = cliente(6800, 180000, 25, 900);
        assertThatThrownBy(() -> d.chat("s", "u")).satisfies(e -> assertThat(e.getMessage()).doesNotContain(CLAVE));
    }

    @Test
    void sinClaveNoEstaHabilitado() {
        assertThat(new GroqClient("", "m", "http://127.0.0.1:1", 1, new Cupo(1, 1, 1, 1, reloj::get)).habilitado()).isFalse();
        assertThat(cliente(1, 1, 1, 1).habilitado()).isTrue();
    }
}
