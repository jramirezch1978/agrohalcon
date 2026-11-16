package pe.halcondorado.allpashift.api;

import java.util.Map;
import java.util.Objects;
import java.util.Set;

import org.springframework.http.HttpStatus;

/**
 * Lo que el agricultor elige en la app (todo opcional): su prioridad y el suelo de su parcela.
 * prioridad   ahorrar_agua | arriesgar_menos | cuidar_suelo   (sin dato → Python usa la de por defecto)
 * tipoSuelo   arenoso | franco | arcilloso
 * salinidad   no | leve | alta                                 (siempre dato del agricultor)
 * fuenteSuelo soilgrids | agricultor                           (de dónde salió tipoSuelo; nunca es dato NASA)
 * aguaDisponible poca | normal | suficiente                  (restricción del agricultor: agua de riego que tiene)
 * escenario   seco | normal | lluvioso                         ("¿y si el año viene…?", hipotético; normal no se envía)
 * ninoHipotetico -2.0 … 5.0 °C                                 ("¿y si el mar sube?": anomalía HIPOTÉTICA de Niño 1+2)
 */
public record PerfilAgricultor(String prioridad, String tipoSuelo, String salinidad, String fuenteSuelo, String aguaDisponible,
                               String escenario, Double ninoHipotetico) {

    public static final PerfilAgricultor VACIO = new PerfilAgricultor(null, null, null, null, null, null, null);
    static final double NINO_MIN = -2.0;
    static final double NINO_MAX = 5.0;

    static final Set<String> PRIORIDADES = Set.of("ahorrar_agua", "arriesgar_menos", "cuidar_suelo");
    static final Set<String> TIPOS_SUELO = Set.of("arenoso", "franco", "arcilloso");
    static final Set<String> SALINIDADES = Set.of("no", "leve", "alta");
    static final Set<String> FUENTES_SUELO = Set.of("soilgrids", "agricultor");
    static final Set<String> AGUA = Set.of("poca", "normal", "suficiente");
    static final Set<String> ESCENARIOS = Set.of("seco", "normal", "lluvioso");

    /** Valida lo que llega por la API: vacío → null; valor desconocido → 400. */
    public static PerfilAgricultor de(String prioridad, String tipoSuelo, String salinidad, String fuenteSuelo) {
        return de(prioridad, tipoSuelo, salinidad, fuenteSuelo, null);
    }

    public static PerfilAgricultor de(String prioridad, String tipoSuelo, String salinidad, String fuenteSuelo,
                                      String aguaDisponible) {
        return de(prioridad, tipoSuelo, salinidad, fuenteSuelo, aguaDisponible, null);
    }

    public static PerfilAgricultor de(String prioridad, String tipoSuelo, String salinidad, String fuenteSuelo,
                                      String aguaDisponible, String escenario) {
        return de(prioridad, tipoSuelo, salinidad, fuenteSuelo, aguaDisponible, escenario, null);
    }

    public static PerfilAgricultor de(String prioridad, String tipoSuelo, String salinidad, String fuenteSuelo,
                                      String aguaDisponible, String escenario, Double ninoHipotetico) {
        if (ninoHipotetico != null && (ninoHipotetico.isNaN() || ninoHipotetico < NINO_MIN || ninoHipotetico > NINO_MAX)) {
            throw new ErroresApi.ApiError(HttpStatus.BAD_REQUEST, "parametro_invalido",
                    "ninoHipotetico debe estar entre " + NINO_MIN + " y " + NINO_MAX + " °C");
        }
        String esc = valor("escenario", escenario, ESCENARIOS);
        String tipo = valor("tipoSuelo", tipoSuelo, TIPOS_SUELO);
        String fuente = valor("fuenteSuelo", fuenteSuelo, FUENTES_SUELO);
        return new PerfilAgricultor(valor("prioridad", prioridad, PRIORIDADES), tipo, valor("salinidad", salinidad, SALINIDADES),
                tipo == null ? null : (fuente == null ? "agricultor" : fuente), valor("aguaDisponible", aguaDisponible, AGUA),
                "normal".equals(esc) ? null : esc, ninoHipotetico);
    }

    private static String valor(String nombre, String v, Set<String> permitidos) {
        if (v == null || v.isBlank()) return null;
        if (!permitidos.contains(v)) {
            throw new ErroresApi.ApiError(HttpStatus.BAD_REQUEST, "parametro_invalido", nombre + " debe ser uno de " + permitidos);
        }
        return v;
    }

    /** Parte de la clave de la consulta guardada en la BD (otro perfil = otra recomendación). */
    public String clave() {
        return String.join(",", Objects.toString(prioridad, "-"), Objects.toString(tipoSuelo, "-"),
                Objects.toString(salinidad, "-"), Objects.toString(fuenteSuelo, "-"))
                + (aguaDisponible == null ? "" : ",agua=" + aguaDisponible)
                + (escenario == null ? "" : ",esc=" + escenario)
                + (ninoHipotetico == null ? "" : String.format(java.util.Locale.ROOT, ",nino=%.1f", ninoHipotetico));
    }

    /** Agrega al pedido de Python solo los campos que tienen dato. */
    public void ponerEn(Map<String, Object> pedido) {
        if (prioridad != null) pedido.put("prioridad", prioridad);
        if (tipoSuelo != null) pedido.put("tipoSuelo", tipoSuelo);
        if (salinidad != null) pedido.put("salinidad", salinidad);
        if (fuenteSuelo != null) pedido.put("fuenteSuelo", fuenteSuelo);
        if (aguaDisponible != null) pedido.put("aguaDisponible", aguaDisponible);
        if (escenario != null) pedido.put("escenario", escenario);
        if (ninoHipotetico != null) pedido.put("ninoHipotetico", ninoHipotetico);
    }
}
