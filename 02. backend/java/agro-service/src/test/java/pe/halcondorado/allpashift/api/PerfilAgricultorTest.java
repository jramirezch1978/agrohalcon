package pe.halcondorado.allpashift.api;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.LinkedHashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;

/** Prioridad y suelo del agricultor: opcionales, validados y parte de la clave de la consulta guardada. */
class PerfilAgricultorTest {

    @Test
    void vacioNoAgregaNadaAlPedido() {
        Map<String, Object> pedido = new LinkedHashMap<>();
        PerfilAgricultor.de(null, "", null, null).ponerEn(pedido);
        assertThat(pedido).isEmpty();
        assertThat(PerfilAgricultor.VACIO.clave()).isEqualTo("-,-,-,-");
    }

    @Test
    void completoVaAPythonYCambiaLaClave() {
        var p = PerfilAgricultor.de("cuidar_suelo", "arenoso", "leve", "soilgrids");
        Map<String, Object> pedido = new LinkedHashMap<>();
        p.ponerEn(pedido);
        assertThat(pedido).containsEntry("prioridad", "cuidar_suelo").containsEntry("tipoSuelo", "arenoso")
                .containsEntry("salinidad", "leve").containsEntry("fuenteSuelo", "soilgrids");
        assertThat(p.clave()).isNotEqualTo(PerfilAgricultor.de("ahorrar_agua", "arenoso", "leve", "soilgrids").clave());
    }

    @Test
    void tipoDeSueloSinFuenteEsDatoDelAgricultor() {
        assertThat(PerfilAgricultor.de(null, "franco", null, null).fuenteSuelo()).isEqualTo("agricultor");
        assertThat(PerfilAgricultor.de(null, null, null, "soilgrids").fuenteSuelo()).isNull();   // sin tipo, la fuente no aplica
    }

    @Test
    void valorDesconocidoEs400() {
        assertThatThrownBy(() -> PerfilAgricultor.de("ganar_mas", null, null, null)).isInstanceOf(ErroresApi.ApiError.class);
        assertThatThrownBy(() -> PerfilAgricultor.de(null, "rocoso", null, null)).isInstanceOf(ErroresApi.ApiError.class);
        assertThatThrownBy(() -> PerfilAgricultor.de(null, null, "mucha", null)).isInstanceOf(ErroresApi.ApiError.class);
    }

    @Test
    void escenarioVaAPythonYNormalNoSeEnvia() {
        Map<String, Object> pedido = new LinkedHashMap<>();
        var seco = PerfilAgricultor.de(null, null, null, null, null, "seco");
        seco.ponerEn(pedido);
        assertThat(pedido).containsEntry("escenario", "seco");
        assertThat(seco.clave()).isNotEqualTo(PerfilAgricultor.VACIO.clave());
        assertThat(PerfilAgricultor.de(null, null, null, null, null, "normal").escenario()).isNull();
        assertThatThrownBy(() -> PerfilAgricultor.de(null, null, null, null, null, "catastrofe")).isInstanceOf(ErroresApi.ApiError.class);
    }

    @Test
    void ninoHipoteticoSeValidaYCambiaLaClave() {
        Map<String, Object> pedido = new LinkedHashMap<>();
        var sim = PerfilAgricultor.de(null, null, null, null, null, null, 3.5);
        sim.ponerEn(pedido);
        assertThat(pedido).containsEntry("ninoHipotetico", 3.5);
        assertThat(sim.clave()).endsWith(",nino=3.5").isNotEqualTo(PerfilAgricultor.VACIO.clave());
        assertThatThrownBy(() -> PerfilAgricultor.de(null, null, null, null, null, null, 9.0)).isInstanceOf(ErroresApi.ApiError.class);
        assertThatThrownBy(() -> PerfilAgricultor.de(null, null, null, null, null, null, Double.NaN)).isInstanceOf(ErroresApi.ApiError.class);
    }
}
