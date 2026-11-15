package pe.halcondorado.allpashift.calculos;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import pe.halcondorado.allpashift.api.JsonUtil;
import pe.halcondorado.allpashift.api.RecomendacionService;
import pe.halcondorado.allpashift.calculos.CalculosClient.CalculosNoDisponibleException;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.ConsultasRepository;
import pe.halcondorado.allpashift.catalogo.ConsultasRepository.Guardada;
import tools.jackson.databind.json.JsonMapper;

/** Integración Java ↔ servicio de cálculos: traducción del catálogo y respaldo desde la BD. */
class IntegracionCalculosTest {

    @Test
    void codigoDelCultivoSinTildesNiEspacios() {
        assertThat(CatalogoCalculos.codigo("Banano organico")).isEqualTo("banano_organico");
        assertThat(CatalogoCalculos.codigo("Limón")).isEqualTo("limon");
        assertThat(CatalogoCalculos.codigo("Maíz amarillo duro")).isEqualTo("maiz_amarillo_duro");
    }

    @Test
    void nombresConTildesYEnIngles() {
        assertThat(NombresCultivo.es("Frijol caupi")).isEqualTo("Frijol caupí");
        assertThat(NombresCultivo.en("Frijol caupi")).isEqualTo("Cowpea");
        assertThat(NombresCultivo.es("Limon")).isEqualTo("Limón");
        assertThat(NombresCultivo.en("Cana de azucar")).isEqualTo("Sugarcane");
        assertThat(NombresCultivo.es("Cultivo nuevo")).isEqualTo("Cultivo nuevo");   // si no está, el de la base
        // el código interno no cambia (sale del nombre de la base)
        assertThat(CatalogoCalculos.codigo("Frijol caupi")).isEqualTo("frijol_caupi");
    }

    @Test
    void aguaDeLaBdAlFormatoDelCalculo() {
        assertThat(CatalogoCalculos.agua("baja")).isEqualTo("bajo");
        assertThat(CatalogoCalculos.agua("media")).isEqualTo("medio");
        assertThat(CatalogoCalculos.agua("alta")).isEqualTo("alto");
    }

    @Test
    void calendarioDeDoceLetrasAEtapas() {
        var etapas = CatalogoCalculos.etapas("KKKDCCCFFCCK", Map.of("K", "Cosecha", "D", "Descanso / poda", "C", "Crecimiento", "F", "Floracion"));
        assertThat(etapas).extracting(e -> e.get("id")).containsExactly("K", "D", "C", "F");
        assertThat(etapas.get(0).get("meses")).isEqualTo(List.of(1, 2, 3, 12));
        assertThat(((Map<?, ?>) etapas.get(3).get("nombre")).get("en")).isEqualTo("flowering");
    }

    // ---------- Respaldo (doc 29, regla 5: primero la BD) ----------

    RecomendacionService servicio(ConsultasRepository consultas) {
        return new RecomendacionService(mock(CatalogoRepository.class), consultas, new JsonUtil(JsonMapper.builder().build()),
                mock(CalculosClient.class), mock(CatalogoCalculos.class));
    }

    @Test
    void datoFrescoEnLaBdNoLlamaAPython() {
        ConsultasRepository consultas = mock(ConsultasRepository.class);
        when(consultas.buscar(eq("k"), eq(Duration.ofHours(3)))).thenReturn(new Guardada("{\"a\":1}", null));
        var r = servicio(consultas).primeroBd("recomendacion", "k", Duration.ofHours(3), 0, 0, null,
                () -> { throw new AssertionError("no debía llamar a Python"); });
        assertThat(r.datos()).containsEntry("a", 1);
        assertThat(r.desdeCache()).isFalse();
    }

    @Test
    void pythonCaidoConDatoViejoEnLaBdDevuelveRespaldo() {
        ConsultasRepository consultas = mock(ConsultasRepository.class);
        when(consultas.buscar(eq("k"), eq(Duration.ofHours(3)))).thenReturn(null);
        when(consultas.buscar(eq("k"), eq(Duration.ofDays(3650)))).thenReturn(new Guardada("{\"fecha\":\"2026-11-10\"}", null));
        var r = servicio(consultas).primeroBd("recomendacion", "k", Duration.ofHours(3), 0, 0, null,
                () -> { throw new CalculosNoDisponibleException("timeout", null); });
        assertThat(r.desdeCache()).isTrue();
        assertThat(r.datos()).containsEntry("fecha", "2026-11-10");
    }

    @Test
    void pythonCaidoSinNadaGuardadoLanza503() {
        ConsultasRepository consultas = mock(ConsultasRepository.class);
        when(consultas.buscar(anyString(), any())).thenReturn(null);
        assertThatThrownBy(() -> servicio(consultas).primeroBd("recomendacion", "k", Duration.ofHours(3), 0, 0, null,
                () -> { throw new CalculosNoDisponibleException("Connection refused", null); }))
                .isInstanceOf(CalculosNoDisponibleException.class);
    }
}
