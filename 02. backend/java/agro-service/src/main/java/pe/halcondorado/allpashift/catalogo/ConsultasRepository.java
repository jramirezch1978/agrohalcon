package pe.halcondorado.allpashift.catalogo;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

/**
 * Lectura y grabación de resultados (regla de arquitectura, doc 29): SOLO Java toca PostgreSQL.
 * - agro.consultas: cada cálculo con su clave (punto + parámetros) → se responde desde aquí si está fresco.
 * - nasa.datos_nasa: los datos NASA que descargó Python.
 * - agro.riesgo_mensual: la perspectiva de la campaña por valle.
 */
@Repository
public class ConsultasRepository {

    private final JdbcTemplate jdbc;

    public ConsultasRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public record Guardada(String resultado, String contrato) {}

    /** Último resultado con esa clave más nuevo que 'frescura'; null si no hay. */
    public Guardada buscar(String clave, Duration frescura) {
        List<Guardada> r = jdbc.query("""
                SELECT resultado::text, contrato::text FROM agro.consultas
                 WHERE clave = ? AND creado_en > now() - make_interval(secs => ?)
                 ORDER BY creado_en DESC LIMIT 1""",
                (rs, i) -> new Guardada(rs.getString(1), rs.getString(2)), clave, (double) frescura.toSeconds());
        return r.isEmpty() ? null : r.get(0);
    }

    @Transactional
    public void guardar(String tipo, String clave, double lat, double lon, Integer zonaId, Integer rotacionId,
                        String indicadoresJson, String resultadoJson, String contratoJson,
                        List<Map<String, Object>> datosNasa) {
        jdbc.update("""
                INSERT INTO agro.consultas (lat, lon, fecha, rotacion_recomendada_id, zona_id, indicadores, resultado, tipo, clave, contrato)
                VALUES (?, ?, current_date, ?, ?, CAST(? AS jsonb), CAST(? AS jsonb), ?, ?, CAST(? AS jsonb))""",
                lat, lon, rotacionId, zonaId, indicadoresJson, resultadoJson, tipo, clave, contratoJson);
        if (datosNasa != null) {
            for (Map<String, Object> f : datosNasa) {
                jdbc.update("""
                        INSERT INTO nasa.datos_nasa (lat, lon, fecha, fuente, variable, valor, version, zona_id)
                        VALUES (?, ?, CAST(? AS date), ?, ?, ?, ?, ?)""",
                        ((Number) f.get("lat")).doubleValue(), ((Number) f.get("lon")).doubleValue(), f.get("fecha"), f.get("fuente"),
                        f.get("variable"), ((Number) f.get("valor")).doubleValue(), f.get("version"), zonaId);
            }
        }
    }

    public void guardarRiesgoMes(int zonaId, int cultivoId, int anio, int mes, String nivel, String motivo) {
        String color = switch (nivel) { case "alto" -> "rojo"; case "medio" -> "ambar"; default -> "verde"; };
        jdbc.update("""
                INSERT INTO agro.riesgo_mensual (zona_id, cultivo_id, anio, mes, nivel, motivo)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (zona_id, cultivo_id, anio, mes) DO UPDATE SET nivel = EXCLUDED.nivel, motivo = EXCLUDED.motivo, calculado_en = now()""",
                zonaId, cultivoId, anio, mes, color, motivo);
    }
}
