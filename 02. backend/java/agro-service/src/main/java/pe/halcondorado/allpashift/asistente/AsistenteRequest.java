package pe.halcondorado.allpashift.asistente;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * POST /api/asistente (contrato que ya usa el frontend):
 * {lat, lon, pregunta, idioma, tipoCultivo, mesSiembra | cultivo}
 */
public record AsistenteRequest(
        @NotNull(message = "lat es obligatoria")
        @DecimalMin(value = "-90", message = "lat debe estar entre -90 y 90")
        @DecimalMax(value = "90", message = "lat debe estar entre -90 y 90") Double lat,

        @NotNull(message = "lon es obligatoria")
        @DecimalMin(value = "-180", message = "lon debe estar entre -180 y 180")
        @DecimalMax(value = "180", message = "lon debe estar entre -180 y 180") Double lon,

        @NotNull(message = "pregunta es obligatoria")
        @Size(min = 3, max = 300, message = "pregunta debe tener entre 3 y 300 caracteres")
        @Pattern(regexp = "(?s)^\\S(.*\\S)?$", message = "pregunta no puede empezar ni terminar con espacios") String pregunta,

        @Pattern(regexp = "es|en", message = "idioma debe ser 'es' o 'en'") String idioma,

        @Pattern(regexp = "temporal|permanente", message = "tipoCultivo debe ser 'temporal' o 'permanente'") String tipoCultivo,

        @Pattern(regexp = "\\d{4}-(0[1-9]|1[0-2])", message = "mesSiembra debe ser AAAA-MM") String mesSiembra,

        @Pattern(regexp = "[a-z_]{2,40}", message = "cultivo no válido") String cultivo) {

    public String idiomaOEs() {
        return idioma == null ? "es" : idioma;
    }
}
