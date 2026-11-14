package pe.halcondorado.allpashift.asistente;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;

import pe.halcondorado.allpashift.api.ErroresApi;
import pe.halcondorado.allpashift.api.JsonUtil;
import pe.halcondorado.allpashift.api.RecomendacionService;
import pe.halcondorado.allpashift.api.RecomendacionService.Respuesta;
import pe.halcondorado.allpashift.calculos.CalculosClient;
import pe.halcondorado.allpashift.calculos.CalculosClient.CalculosNoDisponibleException;
import tools.jackson.databind.json.JsonMapper;

/** Fase 3: asistente con Python (RecomendacionService) y Groq simulados. Sin base de datos. */
class AsistenteTest {

    /** Recomendación con la misma forma que devuelve el servicio de cálculos. */
    static final Map<String, Object> REC = Map.of(
            "indicadores", Map.of(
                    "lluvia", Map.of("valor", 0.59, "normal", 0.09, "unidad", "mm/día", "nivel", "bajo", "fuente", "GPM IMERG"),
                    "calor", Map.of("valor", 33.3, "normal", 32.5, "unidad", "°C", "nivel", "bajo", "fuente", "NASA POWER"),
                    "elNino", Map.of("valor", 6.0, "normal", 0.0, "unidad", "°C anomalía", "nivel", "alto", "fuente", "MUR SST")),
            "rotaciones", List.of(Map.of("nombre", "Arroz - Frijol", "puntaje", 90, "riesgo", "bajo", "usoAgua", "alto",
                    "explicacion", "Pierde 10 puntos.",
                    "descuentos", List.of(Map.of("indicador", "calor", "puntos", -10, "fuente", "NASA POWER", "regla", "temperatura")),
                    "ciclo", Map.of("mesMasRiesgoso", "2027-01", "meses", List.of(
                            Map.of("mes", "2027-01", "riesgo", "medio", "motivo", "El Niño", "fuente", "NASA POWER + MUR SST",
                                    "componentes", Map.of("calor", "bajo")))))),
            "queHacer", Map.of("tipo", "preparar drenaje", "accion", "Prepara los drenajes",
                    "motivo", "El mar está +6.0 °C sobre lo normal.", "fuente", "MUR SST"));
    static final List<String> FUENTES_JSON = List.of("GPM IMERG", "NASA POWER", "MUR SST");

    RecomendacionService recos;
    GroqClient groq;
    AsistenteService servicio;
    MockMvc mvc;

    @BeforeEach
    void preparar() {
        recos = mock(RecomendacionService.class);
        groq = mock(GroqClient.class);
        when(recos.recomendacion(any(Double.class), any(Double.class), anyString(), any(), any(), any()))
                .thenReturn(new Respuesta(REC, false));
        when(groq.habilitado()).thenReturn(true);
        servicio = new AsistenteService(recos, groq, new JsonUtil(JsonMapper.builder().build()), 1); // timeout 1 s en pruebas
        LocalValidatorFactoryBean validador = new LocalValidatorFactoryBean();
        validador.afterPropertiesSet();
        mvc = MockMvcBuilders.standaloneSetup(new AsistenteController(servicio, new LimitadorPreguntas(), mock(CalculosClient.class)))
                .setControllerAdvice(new ErroresApi()).setValidator(validador).build();
    }

    static AsistenteRequest pregunta(String texto) {
        return new AsistenteRequest(-5.19, -80.63, texto, "es", "temporal", "2026-12", null);
    }

    // 1
    @Test
    void respuestaNormalModoIaConFuentesCorrectas() {
        when(groq.chat(anyString(), anyString())).thenReturn("El mar está +6.0 °C (MUR SST) y la lluvia de GPM IMERG es baja.");
        AsistenteRespuesta r = servicio.responder(pregunta("¿Por qué no me conviene sembrar arroz?"));
        assertThat(r.modo()).isEqualTo("ia");
        assertThat(r.fuentes()).containsExactlyInAnyOrder("GPM IMERG", "MUR SST");
        // La pregunta va en el mensaje de usuario, nunca en el de sistema; el JSON va reducido (sin "componentes")
        verify(groq).chat(argThat(s -> !s.contains("arroz")),
                argThat(u -> u.contains("Pregunta del agricultor: ¿Por qué no me conviene sembrar arroz?") && !u.contains("componentes")));
    }

    // 2
    @Test
    void groqLentoUsaRespaldo() {
        when(groq.chat(anyString(), anyString())).thenAnswer(i -> { Thread.sleep(2500); return "tarde"; });
        AsistenteRespuesta r = servicio.responder(pregunta("¿Qué hago?"));
        assertThat(r.modo()).isEqualTo("respaldo");
        assertThat(r.respuesta()).isEqualTo("Prepara los drenajes. El mar está +6.0 °C sobre lo normal.");
        assertThat(r.fuentes()).containsExactly("MUR SST");
    }

    // 3
    @Test
    void groqError500UsaRespaldo() {
        when(groq.chat(anyString(), anyString())).thenThrow(new GroqClient.GroqException("groq_error_HttpServerErrorException"));
        assertThat(servicio.responder(pregunta("¿Qué hago?")).modo()).isEqualTo("respaldo");
    }

    // 4
    @Test
    void respuestaQueMencionaSmapModisONdviUsaRespaldo() {
        for (String t : List.of("Según SMAP el suelo está seco.", "MODIS muestra plantas verdes.", "El ndvi es bajo.")) {
            when(groq.chat(anyString(), anyString())).thenReturn(t);
            assertThat(servicio.responder(pregunta("¿Cómo está mi campo?")).modo()).isEqualTo("respaldo");
        }
    }

    // 5
    @Test
    void fuentesNuncaTieneAlgoQueNoEsteEnElJson() {
        when(groq.chat(anyString(), anyString())).thenReturn("Según SENAMHI y NASA POWER, el calor es normal.");
        AsistenteRespuesta r = servicio.responder(pregunta("¿Hace calor?"));
        assertThat(r.fuentes()).containsExactly("NASA POWER").allMatch(FUENTES_JSON::contains);
        when(groq.chat(anyString(), anyString())).thenReturn("Prepara los drenajes antes de sembrar.");
        assertThat(servicio.responder(pregunta("¿Qué hago?")).fuentes()).containsExactly("MUR SST"); // ninguna citada
        assertThat(AsistenteService.fuentesDelJson(AsistenteService.reducir(REC))).containsExactlyInAnyOrderElementsOf(FUENTES_JSON);
    }

    @Test
    void respuestaVaciaOLargaUsaRespaldo() {
        assertThat(AsistenteService.validar("")).isEqualTo("respuesta_vacia");
        assertThat(AsistenteService.validar("a".repeat(801))).isEqualTo("respuesta_larga");
        assertThat(AsistenteService.validar("Prepara los drenajes (MUR SST).")).isNull();
    }

    @Test
    void sinClaveDeGroqRespondeRespaldoSinLlamarALaIa() {
        when(groq.habilitado()).thenReturn(false);
        assertThat(servicio.responder(pregunta("¿Qué hago?")).modo()).isEqualTo("respaldo");
        verify(groq, never()).chat(anyString(), anyString());
    }

    // 6
    @Test
    void preguntaVaciaLargaOConEspaciosDa400() throws Exception {
        for (String p : List.of("", "a".repeat(301), "  hola  ")) {
            mvc.perform(post("/api/asistente").contentType(MediaType.APPLICATION_JSON)
                            .content("{\"lat\":-5.19,\"lon\":-80.63,\"pregunta\":\"" + p + "\",\"idioma\":\"es\"}")
                            .with(r -> { r.setRemoteAddr("10.0.6." + p.length()); return r; }))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error").value("parametro_invalido"));
        }
    }

    // 7
    @Test
    void laPreguntaOnceEnUnMinutoDa429() throws Exception {
        when(groq.habilitado()).thenReturn(false);
        String cuerpo = "{\"lat\":-5.19,\"lon\":-80.63,\"pregunta\":\"¿Qué hago?\",\"idioma\":\"es\"}";
        for (int i = 0; i < 10; i++) {
            mvc.perform(post("/api/asistente").contentType(MediaType.APPLICATION_JSON).content(cuerpo)
                    .with(r -> { r.setRemoteAddr("192.168.7.7"); return r; })).andExpect(status().isOk());
        }
        mvc.perform(post("/api/asistente").contentType(MediaType.APPLICATION_JSON).content(cuerpo)
                        .with(r -> { r.setRemoteAddr("192.168.7.7"); return r; }))
                .andExpect(status().isTooManyRequests())
                .andExpect(jsonPath("$.error").value("demasiadas_preguntas"));
    }

    // 8
    @Test
    void pythonCaidoYSinCacheDa503() throws Exception {
        when(recos.recomendacion(any(Double.class), any(Double.class), anyString(), any(), any(), any()))
                .thenThrow(new CalculosNoDisponibleException("Connection refused", null));
        mvc.perform(post("/api/asistente").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"lat\":33.3,\"lon\":44.4,\"pregunta\":\"¿Qué siembro?\",\"idioma\":\"es\"}")
                        .with(r -> { r.setRemoteAddr("10.0.8.8"); return r; }))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error").value("servicio_calculos_no_disponible"));
    }
}
