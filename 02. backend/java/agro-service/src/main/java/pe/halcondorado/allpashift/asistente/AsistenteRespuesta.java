package pe.halcondorado.allpashift.asistente;

import java.util.List;

/** {"respuesta", "fuentes", "modo"}: modo = "ia" (Groq) o "respaldo" (queHacer de la recomendación). */
public record AsistenteRespuesta(String respuesta, List<String> fuentes, String modo) {}
