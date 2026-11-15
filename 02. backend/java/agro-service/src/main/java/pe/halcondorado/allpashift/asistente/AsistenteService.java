package pe.halcondorado.allpashift.asistente;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.function.LongSupplier;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import pe.halcondorado.allpashift.api.JsonUtil;
import pe.halcondorado.allpashift.api.RecomendacionService;

/**
 * Asistente: la IA SOLO explica la recomendación ya calculada por el servicio de cálculos. Nunca calcula, nunca
 * inventa números, cultivos ni fuentes, y nunca decide qué sembrar.
 * 1) Recomendación con el MISMO servicio que /api/recomendacion (BD primero, luego Python; 503 si no hay).
 * 2) JSON reducido. 3) Groq con timeout de 8 s. 4) Se valida la respuesta. Cualquier fallo → respaldo.
 */
@Service
public class AsistenteService {

    private static final Logger log = LoggerFactory.getLogger(AsistenteService.class);
    static final int MAX_CARACTERES_RESPUESTA = 800;
    /** Datos que AllpaShift NO usa: si la IA los menciona, está inventando → respaldo. */
    /** Una respuesta buena de la IA se guarda 30 min: las preguntas sugeridas se repiten y el cupo gratuito de Groq es muy corto. */
    static final long CACHE_VIGENCIA_MS = 30 * 60 * 1000L;
    static final int CACHE_MAXIMO = 300;
    static final Pattern NUMERO = Pattern.compile("(?<![\\w.])(\\d+(?:[.,]\\d+)?)");
    static final Pattern DATOS_NO_USADOS = Pattern.compile("\\b(SMAP|MODIS|NDVI)\\b", Pattern.CASE_INSENSITIVE);
    /** El agricultor no sabe qué es un JSON: "(fuente: JSON)" no es una fuente (se vio en producción el 14-nov). */
    static final Pattern MENCIONA_JSON = Pattern.compile("\\bJSON\\b", Pattern.CASE_INSENSITIVE);

    static final String SISTEMA_ES = "Eres el asistente de AllpaShift, una app que ayuda a agricultores con datos de la NASA. "
            + "Responde en español, en palabras simples, en máximo 4 frases. Usa SOLO los datos del JSON de la recomendación. "
            + "NO hagas cálculos nuevos, NO inventes números, cultivos, fechas ni fuentes, y NO cambies la recomendación. "
            + "Cuando uses un dato, nombra su fuente tal como aparece en el JSON (por ejemplo NASA POWER o MUR SST). Si la pregunta no se puede responder con el JSON, "
            + "dilo y sugiere revisar la pantalla de la app. Si preguntan algo que no es de agricultura o clima, responde amablemente "
            + "que solo puedes ayudar con la recomendación de su parcela. Nunca escribas la palabra JSON (ni \"fuente: JSON\"): di \"los datos de tu parcela\".";
    static final String SISTEMA_EN = "You are the AllpaShift assistant, an app that helps farmers with NASA data. "
            + "Answer in English, in simple words, in at most 4 sentences. Use ONLY the data in the recommendation JSON. "
            + "Do NOT make new calculations, do NOT invent numbers, crops, dates or sources, and do NOT change the recommendation. "
            + "When you use a value, name its source exactly as it appears in the JSON (for example NASA POWER or MUR SST). If the question cannot be answered with the JSON, "
            + "say so and suggest checking the app screen. If they ask about something that is not farming or climate, kindly answer "
            + "that you can only help with the recommendation for their plot. Never write the word JSON (nor \"source: JSON\"): say \"your plot's data\".";

    private final RecomendacionService recomendaciones;
    private final GroqClient groq;
    private final JsonUtil json;
    private final int timeoutSegundos;
    private final Map<String, Guardada> cache = new java.util.LinkedHashMap<>(16, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, Guardada> eldest) {
            return size() > CACHE_MAXIMO;
        }
    };
    private LongSupplier reloj = System::currentTimeMillis;

    private record Guardada(AsistenteRespuesta respuesta, long expiraMs) {}

    public AsistenteService(RecomendacionService recomendaciones, GroqClient groq, JsonUtil json,
                            @Value("${GROQ_TIMEOUT_SEGUNDOS:8}") int timeoutSegundos) {
        this.recomendaciones = recomendaciones;
        this.groq = groq;
        this.json = json;
        this.timeoutSegundos = timeoutSegundos;
    }

    public AsistenteRespuesta responder(AsistenteRequest p) {
        long inicio = System.currentTimeMillis();
        String idioma = p.idiomaOEs();

        // 1) La recomendación ya calculada (CalculosNoDisponibleException → 503 si Python está caído y no hay dato)
        Map<String, Object> rec = recomendaciones.recomendacion(p.lat(), p.lon(), idioma, p.tipoCultivo(),
                p.mesSiembra(), p.cultivo()).datos();
        Map<String, Object> reducido = reducir(rec);

        // 2-4) IA o respaldo. Misma pregunta sobre la misma recomendación → la respuesta guardada (no gasta cupo de Groq)
        String clave = claveCache(idioma, p.pregunta(), reducido);
        AsistenteRespuesta guardada = buscarEnCache(clave);
        if (guardada != null) {
            registrar(idioma, p.pregunta(), "ia_cache", inicio, null);
            return guardada;
        }
        String motivo;
        if (!groq.habilitado()) {
            motivo = "groq_desactivado";
        } else {
            try {
                String texto = llamarConLimite(idioma, reducido, p.pregunta());
                motivo = validar(texto, reducido);
                if (motivo == null) {
                    AsistenteRespuesta r = new AsistenteRespuesta(texto.trim(), fuentesMencionadas(texto, reducido), "ia");
                    guardarEnCache(clave, r);
                    registrar(idioma, p.pregunta(), r.modo(), inicio, null);
                    return r;
                }
            } catch (TimeoutException e) {
                motivo = "timeout_" + timeoutSegundos + "s";
            } catch (ExecutionException e) {
                motivo = e.getCause() instanceof GroqClient.GroqException g ? g.getMessage() : "error_groq";
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                motivo = "interrumpido";
            }
        }
        AsistenteRespuesta r = respaldo(reducido);
        registrar(idioma, p.pregunta(), r.modo(), inicio, motivo);
        return r;
    }

    private String llamarConLimite(String idioma, Map<String, Object> reducido, String pregunta)
            throws TimeoutException, ExecutionException, InterruptedException {
        boolean en = "en".equals(idioma);
        // La pregunta va SIEMPRE como dato del mensaje de usuario, nunca dentro del mensaje de sistema
        String usuario = (en ? "Calculated recommendation (JSON): " : "Recomendación calculada (JSON): ")
                + json.escribir(reducido)
                + (en ? "\nFarmer's question: " : "\nPregunta del agricultor: ") + pregunta;
        return CompletableFuture.supplyAsync(() -> groq.chat(en ? SISTEMA_EN : SISTEMA_ES, usuario))
                .get(timeoutSegundos, TimeUnit.SECONDS);
    }

    /** null si la respuesta es válida; si no, el motivo para usar el respaldo. */
    static String validar(String texto) {
        if (texto == null || texto.isBlank()) return "respuesta_vacia";
        if (texto.length() > MAX_CARACTERES_RESPUESTA) return "respuesta_larga";
        if (DATOS_NO_USADOS.matcher(texto).find()) return "menciona_dato_no_usado";
        if (MENCIONA_JSON.matcher(texto).find()) return "menciona_json";
        return null;
    }

    /**
     * Como {@link #validar(String)} y además: ningún NÚMERO de la respuesta puede salir de la nada. Solo valen los que están en la
     * recomendación (valores, normales, puntajes, fechas…), sus redondeos, las diferencias y los porcentajes de anomalía de cada
     * indicador, 0 y 100, los años y los conteos del 1 al 10 ("3 rotaciones"). Si no, es un dato inventado → respaldo.
     */
    static String validar(String texto, Map<String, Object> reducido) {
        String basico = validar(texto);
        if (basico != null) return basico;
        List<Double> permitidos = numerosPermitidos(reducido);
        var m = NUMERO.matcher(texto);
        while (m.find()) {
            double v = Double.parseDouble(m.group(1).replace(',', '.'));
            boolean cuentaChica = v <= 10 && v == Math.rint(v);
            boolean anio = v >= 1990 && v <= 2100 && v == Math.rint(v);
            if (!cuentaChica && !anio && permitidos.stream().noneMatch(p -> Math.abs(p - v) < 1e-6)) return "numero_no_respaldado";
        }
        return null;
    }

    /** Todo número que la IA puede decir sin inventar (ver {@link #validar(String, Map)}). */
    @SuppressWarnings("unchecked")
    static List<Double> numerosPermitidos(Map<String, Object> reducido) {
        Set<Double> base = new HashSet<>(Set.of(0.0, 100.0));
        recogerNumeros(reducido, base);
        if (reducido.get("indicadores") instanceof Map<?, ?> inds) {
            for (Object o : inds.values()) {
                if (o instanceof Map<?, ?> i && i.get("valor") instanceof Number v && i.get("normal") instanceof Number n) {
                    base.add(Math.abs(v.doubleValue() - n.doubleValue()));
                    if (n.doubleValue() != 0) base.add(Math.abs(v.doubleValue() / n.doubleValue() - 1) * 100);
                }
            }
        }
        List<Double> con = new ArrayList<>();
        for (double x : base) {
            for (int d = 0; d <= 3; d++) {
                double f = Math.pow(10, d);
                con.add(Math.round(x * f) / f);
                con.add(Math.round(Math.abs(x) * f) / f);
            }
        }
        return con;
    }

    private static void recogerNumeros(Object n, Set<Double> salida) {
        if (n instanceof Number num) {
            salida.add(num.doubleValue());
        } else if (n instanceof String s) {
            var m = NUMERO.matcher(s);
            while (m.find()) salida.add(Double.parseDouble(m.group(1).replace(',', '.')));
        } else if (n instanceof Map<?, ?> mapa) {
            mapa.values().forEach(v -> recogerNumeros(v, salida));
        } else if (n instanceof List<?> lista) {
            lista.forEach(v -> recogerNumeros(v, salida));
        }
    }

    /** Idioma + pregunta sin mayúsculas ni espacios de más + la recomendación: la misma pregunta sobre otros datos NO reutiliza la respuesta. */
    String claveCache(String idioma, String pregunta, Map<String, Object> reducido) {
        String normal = pregunta.trim().toLowerCase(Locale.ROOT).replaceAll("\\s+", " ");
        return idioma + "|" + normal + "|" + json.escribir(reducido).hashCode();
    }

    synchronized AsistenteRespuesta buscarEnCache(String clave) {
        Guardada g = cache.get(clave);
        if (g == null) return null;
        if (reloj.getAsLong() >= g.expiraMs()) {
            cache.remove(clave);
            return null;
        }
        return g.respuesta();
    }

    synchronized void guardarEnCache(String clave, AsistenteRespuesta r) {
        cache.put(clave, new Guardada(r, reloj.getAsLong() + CACHE_VIGENCIA_MS));
    }

    /** Para las pruebas. */
    void usarReloj(LongSupplier reloj) {
        this.reloj = reloj;
    }

    /** "fuentes" = fuentes del JSON que aparecen en el texto; si ninguna, [queHacer.fuente]. Nunca otra. */
    static List<String> fuentesMencionadas(String texto, Map<String, Object> reducido) {
        String t = texto.toLowerCase(Locale.ROOT);
        List<String> mencionadas = fuentesDelJson(reducido).stream().filter(f -> t.contains(f.toLowerCase(Locale.ROOT))).toList();
        return mencionadas.isEmpty() ? List.of(fuenteQueHacer(reducido)) : mencionadas;
    }

    /** Todas las fuentes que aparecen en el JSON ("NASA POWER + MUR SST" cuenta como dos). */
    static Set<String> fuentesDelJson(Object nodo) {
        Set<String> fuentes = new LinkedHashSet<>();
        recorrer(nodo, fuentes);
        return fuentes;
    }

    @SuppressWarnings("unchecked")
    private static void recorrer(Object n, Set<String> fuentes) {
        if (n instanceof Map<?, ?> m) {
            m.forEach((k, v) -> {
                if ("fuente".equals(k) && v instanceof String s) {
                    for (String f : s.split(" \\+ ")) if (!f.isBlank()) fuentes.add(f.trim());
                } else {
                    recorrer(v, fuentes);
                }
            });
        } else if (n instanceof List<?> l) {
            l.forEach(x -> recorrer(x, fuentes));
        }
    }

    @SuppressWarnings("unchecked")
    private static String fuenteQueHacer(Map<String, Object> reducido) {
        Object qh = reducido.get("queHacer");
        return qh instanceof Map<?, ?> m && m.get("fuente") != null ? m.get("fuente").toString() : "";
    }

    /** Respaldo: queHacer.accion + ". " + queHacer.motivo, con su fuente. */
    @SuppressWarnings("unchecked")
    static AsistenteRespuesta respaldo(Map<String, Object> reducido) {
        Map<String, Object> qh = (Map<String, Object>) reducido.getOrDefault("queHacer", Map.of());
        String accion = String.valueOf(qh.getOrDefault("accion", "")).replaceAll("\\.\\s*$", "");
        return new AsistenteRespuesta(accion + ". " + qh.getOrDefault("motivo", ""), List.of(fuenteQueHacer(reducido)), "respaldo");
    }

    /** JSON reducido para la IA: indicadores, queHacer y rotaciones (o plan). Ahorra tokens. */
    @SuppressWarnings("unchecked")
    static Map<String, Object> reducir(Map<String, Object> rec) {
        Map<String, Object> r = new LinkedHashMap<>();

        Map<String, Object> ind = new LinkedHashMap<>();
        ((Map<String, Object>) rec.getOrDefault("indicadores", Map.of())).forEach((clave, v) -> {
            Map<String, Object> i = (Map<String, Object>) v;
            if (i.get("valor") == null) return;   // sin dato: no se manda
            ind.put(clave, solo(i, "valor", "normal", "unidad", "nivel", "fuente"));
        });
        r.put("indicadores", ind);
        r.put("queHacer", solo((Map<String, Object>) rec.getOrDefault("queHacer", Map.of()), "tipo", "accion", "motivo", "fuente"));

        if (rec.get("plan") instanceof Map<?, ?> plan) {
            r.put("plan", solo((Map<String, Object>) plan, "cultivo", "etapaActual", "meses", "acciones"));
        } else {
            List<Map<String, Object>> rots = new ArrayList<>();
            for (Map<String, Object> x : (List<Map<String, Object>>) rec.getOrDefault("rotaciones", List.of())) {
                Map<String, Object> o = solo(x, "nombre", "puntaje", "riesgo", "usoAgua", "explicacion");
                o.put("descuentos", ((List<Map<String, Object>>) x.getOrDefault("descuentos", List.of())).stream()
                        .map(d -> solo(d, "indicador", "puntos", "fuente")).toList());
                Map<String, Object> ciclo = (Map<String, Object>) x.getOrDefault("ciclo", Map.of());
                Map<String, Object> c = new LinkedHashMap<>();
                c.put("mesMasRiesgoso", ciclo.get("mesMasRiesgoso"));
                c.put("meses", ((List<Map<String, Object>>) ciclo.getOrDefault("meses", List.of())).stream()
                        .map(m -> solo(m, "mes", "riesgo", "motivo", "fuente")).toList());
                o.put("ciclo", c);
                rots.add(o);
            }
            r.put("rotaciones", rots);
        }
        return r;
    }

    private static Map<String, Object> solo(Map<String, Object> m, String... claves) {
        Map<String, Object> o = new LinkedHashMap<>();
        for (String k : claves) if (m.containsKey(k)) o.put(k, m.get(k));
        return o;
    }

    /** Log sin la clave, sin la pregunta completa y sin la respuesta completa. */
    private static void registrar(String idioma, String pregunta, String modo, long inicio, String motivo) {
        log.info("asistente idioma={} largoPregunta={} modo={} ms={}{}", idioma, pregunta.length(), modo,
                System.currentTimeMillis() - inicio, motivo == null ? "" : " motivo=" + motivo);
    }

    /** Para /api/salud. */
    public String modo() {
        return groq.habilitado() ? "ia" : "solo_respaldo";
    }
}
