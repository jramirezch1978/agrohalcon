package pe.halcondorado.allpashift.api;

import java.util.Map;

import org.springframework.stereotype.Component;

import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.json.JsonMapper;

/** JSON ↔ Map para guardar resultados en columnas JSONB (Jackson 3, el de Spring Boot 4). */
@Component
public class JsonUtil {

    private final JsonMapper mapper;

    public JsonUtil(JsonMapper mapper) {
        this.mapper = mapper;
    }

    public String escribir(Object o) {
        return o == null ? null : mapper.writeValueAsString(o);
    }

    public Map<String, Object> leer(String s) {
        return mapper.readValue(s, new TypeReference<Map<String, Object>>() {});
    }
}
