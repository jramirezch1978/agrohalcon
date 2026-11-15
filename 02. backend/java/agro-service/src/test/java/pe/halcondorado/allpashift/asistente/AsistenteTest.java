package pe.halcondorado.allpashift.asistente;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
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

    @Test
    void respuestaQueDiceFuenteJsonUsaRespaldo() {
        // visto en producción el 14-nov: "...riesgo bajo según la recomendación (fuente: JSON)."
        when(groq.chat(anyString(), anyString())).thenReturn("El arroz tiene 90 puntos y riesgo bajo (fuente: JSON).");
        assertThat(servicio.responder(pregunta("¿Me conviene el arroz?")).modo()).isEqualTo("respaldo");
        assertThat(AsistenteService.validar("Según el json no hay datos.")).isEqualTo("menciona_json");
        assertThat(AsistenteService.validar("Prepara los drenajes (MUR SST).")).isNull();
    }

    @Test
    void elAsistenteSeLlamaAllpaShiftYPideNoDecirJson() {
        assertThat(AsistenteService.SISTEMA_ES).contains("AllpaShift").doesNotContain("AgroShift").contains("Nunca escribas la palabra JSON");
        assertThat(AsistenteService.SISTEMA_EN).contains("AllpaShift").doesNotContain("AgroShift").contains("Never write the word JSON");
    }

    // 5b: números
    @Test
    void respuestaConUnNumeroInventadoUsaRespaldo() {
        when(groq.chat(anyString(), anyString())).thenReturn("La lluvia será de 87 mm esta semana (GPM IMERG).");
        assertThat(servicio.responder(pregunta("¿Va a llover?")).modo()).isEqualTo("respaldo");
    }

    @Test
    void respuestaConNumerosDeLaRecomendacionPasa() {
        // 6.0 y 90 están en el JSON; 556 % = (0.59 / 0.09 - 1) * 100 es la anomalía de la lluvia; "3 opciones" es una cuenta chica
        when(groq.chat(anyString(), anyString())).thenReturn(
                "El mar está +6.0 °C sobre lo normal (MUR SST) y la lluvia está 556 % sobre lo normal (GPM IMERG). Arroz - Frijol tiene 90 de 100 puntos entre 3 opciones.");
        assertThat(servicio.responder(pregunta("¿Qué pasa?")).modo()).isEqualTo("ia");
    }

    @Test
    void losNumerosPermitidosIncluyenRedondeosDiferenciasYPorcentajes() {
        var permitidos = AsistenteService.numerosPermitidos(AsistenteService.reducir(REC));
        assertThat(permitidos).contains(6.0, 0.59, 0.09, 0.5, 33.3, 32.5, 0.8, 90.0, 10.0, 100.0, 556.0, 555.6);
        assertThat(permitidos).doesNotContain(87.0, 7.0);
        assertThat(AsistenteService.validar("Faltan 0,5 mm/día para llegar a lo normal (GPM IMERG).", AsistenteService.reducir(REC))).isNull();  // coma decimal
        assertThat(AsistenteService.validar("Habrá 45 mm.", AsistenteService.reducir(REC))).isEqualTo("numero_no_respaldado");
        assertThat(AsistenteService.validar("En 2027-01 el riesgo es medio (NASA POWER + MUR SST).", AsistenteService.reducir(REC))).isNull();  // una fecha de la recomendación
    }

    // 5c: caché de respuestas (el cupo gratuito de Groq es muy corto)
    @Test
    void laMismaPreguntaSobreLaMismaRecomendacionNoVuelveAGroq() {
        when(groq.chat(anyString(), anyString())).thenReturn("El mar está +6.0 °C (MUR SST).");
        AsistenteRespuesta a = servicio.responder(pregunta("¿Por qué esa rotación?"));
        AsistenteRespuesta b = servicio.responder(pregunta("¿Por qué esa rotación?"));
        assertThat(a.modo()).isEqualTo("ia");
        assertThat(b).isEqualTo(a);
        verify(groq, times(1)).chat(anyString(), anyString());
    }

    @Test
    void laCacheIgnoraMayusculasYEspaciosPeroNoMezclaPreguntasDistintasNiIdiomas() {
        when(groq.chat(anyString(), anyString())).thenReturn("El mar está +6.0 °C (MUR SST).");
        servicio.responder(pregunta("¿Por qué esa rotación?"));
        servicio.responder(new AsistenteRequest(-5.19, -80.63, "¿POR QUÉ   ESA ROTACIÓN?", "es", "temporal", "2026-12", null));
        verify(groq, times(1)).chat(anyString(), anyString());
        servicio.responder(pregunta("¿Qué significa El Niño?"));
        servicio.responder(new AsistenteRequest(-5.19, -80.63, "¿Por qué esa rotación?", "en", "temporal", "2026-12", null));
        verify(groq, times(3)).chat(anyString(), anyString());
    }

    @Test
    void losRespaldosYLosFallosNoSeGuardanEnCache() {
        when(groq.chat(anyString(), anyString())).thenThrow(new GroqClient.GroqException("groq_429_espera_30s"))
                .thenReturn("El mar está +6.0 °C (MUR SST).");
        assertThat(servicio.responder(pregunta("¿Qué hago?")).modo()).isEqualTo("respaldo");
        assertThat(servicio.responder(pregunta("¿Qué hago?")).modo()).isEqualTo("ia");   // el fallo no quedó guardado
        verify(groq, times(2)).chat(anyString(), anyString());
    }

    @Test
    void laRespuestaGuardadaCaducaALos30Minutos() {
        long[] ahora = {1_000_000L};
        servicio.usarReloj(() -> ahora[0]);
        when(groq.chat(anyString(), anyString())).thenReturn("El mar está +6.0 °C (MUR SST).");
        servicio.responder(pregunta("¿Qué hago?"));
        ahora[0] += AsistenteService.CACHE_VIGENCIA_MS - 1;
        servicio.responder(pregunta("¿Qué hago?"));
        verify(groq, times(1)).chat(anyString(), anyString());
        ahora[0] += 2;
        servicio.responder(pregunta("¿Qué hago?"));
        verify(groq, times(2)).chat(anyString(), anyString());
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

    @Test
    @SuppressWarnings("unchecked")
    void smapValeSiVieneEnLaRecomendacionYUnaFuenteAjenaNo() {
        Map<String, Object> conSmap = new java.util.HashMap<>(REC);
        Map<String, Object> ind = new java.util.HashMap<>((Map<String, Object>) REC.get("indicadores"));
        ind.put("humedadSuelo", Map.of("valor", 0.21, "normal", 0.25, "unidad", "m3/m3", "nivel", "bajo", "fuente", "SMAP"));
        conSmap.put("indicadores", ind);
        var reducido = AsistenteService.reducir(conSmap);
        assertThat(AsistenteService.validar("La humedad del suelo según SMAP está cerca de lo normal.", reducido)).isNull();
        assertThat(AsistenteService.validar("Según MODIS las plantas están bien.", reducido)).isEqualTo("menciona_fuente_ajena");
        assertThat(AsistenteService.validar("El relieve de SRTM muestra zonas bajas.", reducido)).isEqualTo("menciona_fuente_ajena");
        // La palabra inglesa "power" no es la fuente NASA POWER
        assertThat(AsistenteService.fuenteAjena("Water has the power to help.", java.util.Set.of())).isNull();
    }
}
