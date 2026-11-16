package pe.halcondorado.allpashift.asistente;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

/** El límite de preguntas usa la IP que pone nginx, no la que el cliente escribe en X-Forwarded-For. */
class IpClienteTest {

    @Test
    void ignoraElXForwardedForDelCliente() {
        var r = new MockHttpServletRequest();
        r.setRemoteAddr("172.18.0.5");                          // el gateway
        r.addHeader("X-Forwarded-For", "1.2.3.4, 9.9.9.9");     // "1.2.3.4" lo inventó el cliente
        r.addHeader("X-Real-IP", "9.9.9.9");                    // lo sobrescribe nginx con $remote_addr
        assertThat(AsistenteController.ip(r)).isEqualTo("9.9.9.9");
    }

    @Test
    void sinNginxUsaLaIpDeLaConexion() {
        var r = new MockHttpServletRequest();
        r.setRemoteAddr("127.0.0.1");
        r.addHeader("X-Forwarded-For", "1.2.3.4");
        assertThat(AsistenteController.ip(r)).isEqualTo("127.0.0.1");
    }
}
