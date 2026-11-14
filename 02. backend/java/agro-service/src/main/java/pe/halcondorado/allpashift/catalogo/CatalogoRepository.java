package pe.halcondorado.allpashift.catalogo;

import java.sql.Array;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** Catálogo del modelo relacional (doc 26): cultivos, rotaciones, zonas, calendario, acciones y eventos El Niño. */
@Repository
public class CatalogoRepository {

    private final JdbcTemplate jdbc;

    public CatalogoRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public record Cultivo(int id, String nombre, double tempMin, double tempMax, String agua, List<Integer> mesesSiembra,
                          List<Integer> mesesCosecha, Integer cicloDias, boolean toleraSequia, boolean toleraInundacion, String tipo) {}

    public record Rotacion(int id, String nombre, int cultivo1Id, int cultivo2Id, boolean monocultivo) {}

    public record Zona(int id, String nombre, double lat, double lon, String region, String piso) {}

    public record Accion(String fase, String descripcion, String alerta) {}

    public record Evento(String nombre, String tipo, java.time.LocalDate inicio, java.time.LocalDate fin, String descripcion) {}

    public List<Cultivo> cultivos(String piso, boolean soloAnuales) {
        return jdbc.query("""
                SELECT v.id, v.nombre, v.temp_min_c, v.temp_max_c, v.agua_necesaria, v.meses_siembra, v.meses_cosecha,
                       c.ciclo_dias, c.tolera_sequia, c.tolera_inundacion, c.tipo
                  FROM agro.v_cultivos_contrato v JOIN agro.cultivos c ON c.id = v.id
                 WHERE (CAST(? AS text) IS NULL OR EXISTS (SELECT 1 FROM agro.calendario k WHERE k.cultivo_id = c.id AND k.piso = CAST(? AS text)))
                   AND (NOT CAST(? AS boolean) OR c.tipo = 'anual')
                 ORDER BY v.id""",
                (rs, i) -> new Cultivo(rs.getInt(1), rs.getString(2), rs.getDouble(3), rs.getDouble(4), rs.getString(5),
                        enteros(rs.getArray(6)), enteros(rs.getArray(7)), (Integer) rs.getObject(8), rs.getBoolean(9), rs.getBoolean(10), rs.getString(11)),
                piso, piso, soloAnuales);
    }

    public List<Rotacion> rotaciones(String piso) {
        return jdbc.query("SELECT id, nombre, cultivo1_id, cultivo2_id, es_monocultivo FROM agro.rotaciones WHERE piso = ? OR piso IS NULL ORDER BY id",
                (rs, i) -> new Rotacion(rs.getInt(1), rs.getString(2), rs.getInt(3), rs.getInt(4), rs.getBoolean(5)), piso);
    }

    public List<Zona> zonas(String region) {
        return jdbc.query("SELECT id, nombre, lat, lon, region, piso FROM agro.zonas WHERE (CAST(? AS text) IS NULL OR region = CAST(? AS text)) ORDER BY id",
                (rs, i) -> new Zona(rs.getInt(1), rs.getString(2), rs.getDouble(3), rs.getDouble(4), rs.getString(5), rs.getString(6)), region, region);
    }

    /** Calendario general (12 letras S/C/F/K/D) de un cultivo en un piso; null si no hay. */
    public String calendario(int cultivoId, String piso) {
        List<String> r = jdbc.queryForList("SELECT string_agg(fase, '' ORDER BY mes) FROM agro.calendario WHERE cultivo_id = ? AND piso = ? AND zona_id IS NULL",
                String.class, cultivoId, piso);
        return r.isEmpty() ? null : r.get(0);
    }

    public Integer idCultivo(String nombre) {
        List<Integer> r = jdbc.queryForList("SELECT id FROM agro.cultivos WHERE nombre = ?", Integer.class, nombre);
        return r.isEmpty() ? null : r.get(0);
    }

    public List<Accion> acciones(Integer cultivoId) {
        return jdbc.query("SELECT fase, descripcion, alerta_nasa FROM agro.acciones_etapa WHERE cultivo_id = ? OR cultivo_id IS NULL ORDER BY cultivo_id NULLS LAST, id",
                (rs, i) -> new Accion(rs.getString(1), rs.getString(2), rs.getString(3)), cultivoId);
    }

    /** Acción por fase con el indicador NASA que la activa (calor, lluvia, humedad_suelo, ndvi...). */
    public record AccionIndicador(String fase, String descripcion, String indicador) {}

    public List<AccionIndicador> accionesConIndicador(Integer cultivoId) {
        return jdbc.query("SELECT fase, descripcion, indicador FROM agro.acciones_etapa WHERE cultivo_id = ? OR cultivo_id IS NULL ORDER BY cultivo_id NULLS LAST, id",
                (rs, i) -> new AccionIndicador(rs.getString(1), rs.getString(2), rs.getString(3)), cultivoId);
    }

    public Map<String, String> fases() {
        Map<String, String> m = new java.util.HashMap<>();
        jdbc.query("SELECT codigo, nombre FROM agro.fases", rs -> { m.put(rs.getString(1), rs.getString(2)); });
        return m;
    }

    public List<Evento> eventos() {
        return jdbc.query("SELECT nombre, tipo, inicio, fin, descripcion FROM nasa.eventos_enso ORDER BY inicio",
                (rs, i) -> new Evento(rs.getString(1), rs.getString(2), rs.getDate(3).toLocalDate(),
                        rs.getDate(4) == null ? null : rs.getDate(4).toLocalDate(), rs.getString(5)));
    }

    private static List<Integer> enteros(Array a) throws SQLException {
        List<Integer> out = new ArrayList<>();
        if (a == null) return out;
        for (Object o : (Object[]) a.getArray()) out.add(((Number) o).intValue());
        return out;
    }
}
