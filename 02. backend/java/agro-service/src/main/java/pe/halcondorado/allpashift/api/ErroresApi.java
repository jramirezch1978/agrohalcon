package pe.halcondorado.allpashift.api;

import java.util.Map;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import pe.halcondorado.allpashift.calculos.CalculosClient.CalculosNoDisponibleException;

/** Todos los errores de la API como {"error", "detalle"} con el código HTTP correcto. */
@RestControllerAdvice
public class ErroresApi {

    private static final Logger log = LoggerFactory.getLogger(ErroresApi.class);

    /** Error con código HTTP y código corto. */
    public static class ApiError extends RuntimeException {
        final HttpStatus status;
        final String error;

        public ApiError(HttpStatus status, String error, String detalle) {
            super(detalle);
            this.status = status;
            this.error = error;
        }
    }

    static void validarCoordenadas(double lat, double lon) {
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            throw new ApiError(HttpStatus.BAD_REQUEST, "parametro_invalido", "lat debe estar entre -90 y 90 y lon entre -180 y 180");
        }
    }

    static void validarLang(String lang) {
        if (!"es".equals(lang) && !"en".equals(lang)) {
            throw new ApiError(HttpStatus.BAD_REQUEST, "parametro_invalido", "lang debe ser 'es' o 'en'");
        }
    }

    @ExceptionHandler(ApiError.class)
    ResponseEntity<Map<String, String>> api(ApiError e) {
        return ResponseEntity.status(e.status).body(Map.of("error", e.error, "detalle", e.getMessage()));
    }

    /** Python caído y sin dato guardado: nunca se inventan datos. */
    @ExceptionHandler(CalculosNoDisponibleException.class)
    ResponseEntity<Map<String, String>> calculos(CalculosNoDisponibleException e) {
        log.warn("Servicio de cálculos no disponible y sin dato guardado: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of(
                "error", "servicio_calculos_no_disponible",
                "detalle", "El servicio de cálculos no respondió y no hay un dato guardado para esta consulta"));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<Map<String, String>> cuerpo(MethodArgumentNotValidException e) {
        String detalle = e.getBindingResult().getFieldErrors().stream()
                .map(f -> f.getField() + ": " + f.getDefaultMessage()).collect(Collectors.joining("; "));
        return ResponseEntity.badRequest().body(Map.of("error", "parametro_invalido", "detalle", detalle));
    }

    @ExceptionHandler({MissingServletRequestParameterException.class, MethodArgumentTypeMismatchException.class,
            HttpMessageNotReadableException.class})
    ResponseEntity<Map<String, String>> parametros(Exception e) {
        return ResponseEntity.badRequest().body(Map.of("error", "parametro_invalido", "detalle", String.valueOf(e.getMessage())));
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<Map<String, String>> otro(Exception e) {
        log.error("Error en la API", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "error_interno", "detalle", "Ocurrió un error inesperado en la API"));
    }
}
