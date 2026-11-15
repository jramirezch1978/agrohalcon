package pe.halcondorado.allpashift.calculos;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.springframework.stereotype.Service;

import pe.halcondorado.allpashift.catalogo.CatalogoRepository;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Cultivo;
import pe.halcondorado.allpashift.catalogo.CatalogoRepository.Rotacion;

/**
 * Traduce el catálogo de PostgreSQL (doc 26: agro.cultivos, calendario, rotaciones, acciones_etapa) al formato
 * que entiende el servicio de cálculos (campo "catalogo" de POST /calcular):
 * {id, nombre{es,en}, tipo temporal|permanente, temp_min, temp_max, agua bajo|medio|alto, duracion_meses,
 *  meses_siembra, tradicional, etapas[{id, nombre, meses}], acciones[{etapa, si, nivel, accion}]}.
 */
@Service
public class CatalogoCalculos {

    /** Nombre en inglés de las fases del calendario (agro.fases solo tiene español). */
    static final Map<String, String> FASE_EN = Map.of("S", "planting", "C", "growth", "F", "flowering", "K", "harvest", "D", "rest / pruning");
    /** indicador de agro.acciones_etapa → componente de riesgo del cálculo. NDVI no se usa (no se integra MODIS). */
    static final Map<String, String> SI = Map.of("calor", "calor", "lluvia", "lluvia_exceso", "humedad_suelo", "deficit");

    private final CatalogoRepository catalogo;

    public CatalogoCalculos(CatalogoRepository catalogo) {
        this.catalogo = catalogo;
    }

    /** cultivos = lista para Python; idPorCodigo = código enviado → id en la base (para grabar riesgo_mensual). */
    public record Catalogo(List<Map<String, Object>> cultivos, Map<String, Integer> idPorCodigo) {}

    public Catalogo paraPiso(String piso) {
        List<Cultivo> lista = catalogo.cultivos(piso, false);
        if (lista.isEmpty()) lista = catalogo.cultivos(null, false);
        List<Integer> ids = lista.stream().map(Cultivo::id).toList();
        Integer tradicional = catalogo.rotaciones(piso).stream()
                .filter(r -> r.monocultivo() && ids.contains(r.cultivo1Id()))
                .map(Rotacion::cultivo1Id).findFirst().orElse(null);
        Map<String, String> fases = catalogo.fases();

        List<Map<String, Object>> salida = new ArrayList<>();
        Map<String, Integer> idPorCodigo = new LinkedHashMap<>();
        for (Cultivo c : lista) {
            boolean permanente = "permanente".equals(c.tipo());
            Map<String, Object> m = new LinkedHashMap<>();
            String codigo = codigo(c.nombre());
            m.put("id", codigo);
            m.put("nombre", Map.of("es", NombresCultivo.es(c.nombre()), "en", NombresCultivo.en(c.nombre())));
            m.put("tipo", permanente ? "permanente" : "temporal");
            m.put("temp_min", c.tempMin());
            m.put("temp_max", c.tempMax());
            m.put("agua", agua(c.agua()));
            m.put("usoAgua", agua(c.agua()));
            m.put("meses_siembra", c.mesesSiembra());
            m.put("tradicional", tradicional != null && tradicional == c.id());
            if (!permanente) {
                int dias = c.cicloDias() == null ? 120 : c.cicloDias();
                m.put("duracion_meses", Math.max(1, Math.min(24, Math.round(dias / 30f))));
            } else {
                String cal = catalogo.calendario(c.id(), piso);
                if (cal == null) cal = catalogo.calendario(c.id(), "costa");
                m.put("etapas", etapas(cal, fases));
                m.put("acciones", acciones(c.id()));
            }
            salida.add(m);
            idPorCodigo.put(codigo, c.id());
        }
        return new Catalogo(salida, idPorCodigo);
    }

    /** "Banano organico" → "banano_organico" (sin tildes, minúsculas). */
    public static String codigo(String nombre) {
        String s = Normalizer.normalize(nombre, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
        return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "_").replaceAll("^_|_$", "");
    }

    static String agua(String bd) {
        return switch (bd == null ? "" : bd) {
            case "baja" -> "bajo";
            case "alta" -> "alto";
            default -> "medio";
        };
    }

    /** Calendario de 12 letras (S/C/F/K/D, enero..diciembre) → etapas con sus meses. */
    static List<Map<String, Object>> etapas(String calendario, Map<String, String> fases) {
        Map<String, List<Integer>> porFase = new LinkedHashMap<>();
        if (calendario != null) {
            for (int i = 0; i < Math.min(12, calendario.length()); i++) {
                porFase.computeIfAbsent(String.valueOf(calendario.charAt(i)), k -> new ArrayList<>()).add(i + 1);
            }
        }
        List<Map<String, Object>> salida = new ArrayList<>();
        porFase.forEach((fase, meses) -> salida.add(Map.of(
                "id", fase,
                "nombre", Map.of("es", fases.getOrDefault(fase, fase).toLowerCase(Locale.ROOT), "en", FASE_EN.getOrDefault(fase, fase)),
                "meses", meses)));
        return salida;
    }

    private List<Map<String, Object>> acciones(int cultivoId) {
        List<Map<String, Object>> salida = new ArrayList<>();
        for (var a : catalogo.accionesConIndicador(cultivoId)) {
            String si = SI.get(a.indicador());
            if (si == null) continue;   // p. ej. 'ndvi': no se usa
            salida.add(Map.of("etapa", a.fase(), "si", si, "nivel", "medio",
                    "accion", Map.of("es", a.descripcion(), "en", a.descripcion())));
        }
        return salida;
    }
}
