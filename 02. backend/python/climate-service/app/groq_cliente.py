"""Groq desde el servicio Python (decisión del equipo, 14-nov-2026).

- Modelo: `openai/gpt-oss-20b` (licencia Apache 2.0, de código abierto) servido por Groq.
- Se llama desde AQUÍ y no desde la app ni desde el navegador: el código del proyecto es público y la clave no puede estar en él.
  La clave vive solo en la variable de entorno `GROQ_API_KEY` del servidor (`.env` en tu PC, `deploy/vps/.env` en el VPS).
  Nunca se escribe en el código, en las respuestas, en los registros ni en los mensajes de error.
- Si no hay clave, Groq falla, se acaba el tiempo o se pasa el límite de preguntas, el que llama muestra el Plan B (plantillas): nunca se rompe.
- El límite de preguntas protege la cuota: con el código público, cualquiera que llegue al servicio podría gastar la clave.

Referencia (verificada 14-nov-2026): POST https://api.groq.com/openai/v1/chat/completions · `max_completion_tokens` ·
`reasoning_effort` low|medium|high para gpt-oss · `include_reasoning: false` para no recibir el razonamiento · texto en `choices[0].message.content`.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx

try:  # en tu PC la clave puede estar en .env; en Docker llega como variable de entorno (sin python-dotenv)
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # pragma: no cover
    pass

URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_POR_DEFECTO = "openai/gpt-oss-20b"
LICENCIA = "Apache-2.0"
TIMEOUT_S = 20.0
MAX_TOKENS = 900  # gpt-oss gasta parte en razonar: con 'low' sobra para una respuesta de ~120 palabras
log = logging.getLogger("allpashift.groq")
_TRANSPORTE: httpx.BaseTransport | None = None  # las pruebas lo cambian por un httpx.MockTransport (sin internet)


def clave() -> str | None:
    return (os.getenv("GROQ_API_KEY") or "").strip() or None


def modelo() -> str:
    return (os.getenv("GROQ_MODEL") or "").strip() or MODELO_POR_DEFECTO


def disponible() -> bool:
    return clave() is not None


@dataclass
class Resultado:
    texto: str | None
    error: str | None  # motivo corto y SIN datos sensibles; None si salió bien
    modelo: str
    ms: int = 0


def completar(mensajes: list[dict]) -> Resultado:
    """Una llamada a Groq. Nunca lanza: devuelve el motivo del fallo para que el que llama use el Plan B."""
    k, m = clave(), modelo()
    if not k:
        return Resultado(None, "sin clave de Groq (GROQ_API_KEY)", m)
    cuerpo = {
        "model": m, "messages": mensajes, "temperature": 0.2, "max_completion_tokens": MAX_TOKENS,
        "reasoning_effort": "low", "include_reasoning": False,
    }  # fmt: skip
    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=TIMEOUT_S, transport=_TRANSPORTE) as http:
            r = http.post(URL, json=cuerpo, headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
        ms = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            log.warning("Groq respondió HTTP %s", r.status_code)  # solo el código: ni el cuerpo ni las cabeceras
            return Resultado(None, f"Groq respondió HTTP {r.status_code}", m, ms)
        texto = (r.json()["choices"][0]["message"].get("content") or "").strip()
        if not texto:
            return Resultado(None, "Groq devolvió una respuesta vacía", m, ms)
        return Resultado(texto, None, m, ms)
    except httpx.TimeoutException:
        log.warning("Groq no respondió en %.0f s", TIMEOUT_S)
        return Resultado(None, "Groq tardó demasiado", m, int((time.monotonic() - t0) * 1000))
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as e:
        log.warning("Groq falló: %s", type(e).__name__)  # el tipo basta; el mensaje podría incluir la URL con datos
        return Resultado(None, f"Groq falló ({type(e).__name__})", m, int((time.monotonic() - t0) * 1000))


class Limitador:
    """Ventana deslizante en memoria: por cliente y global por minuto, y un tope diario. Protege la cuota de la clave."""

    def __init__(self, por_cliente: int | None = None, global_min: int | None = None, diario: int | None = None, ventana_s: float = 60.0,
                 reloj=time.monotonic, hoy=date.today):  # fmt: skip
        env = lambda n, d: int(os.getenv(n) or d)  # noqa: E731
        self.por_cliente = por_cliente if por_cliente is not None else env("GROQ_MAX_POR_MINUTO_CLIENTE", 8)
        self.global_min = global_min if global_min is not None else env("GROQ_MAX_POR_MINUTO", 40)
        self.diario = diario if diario is not None else env("GROQ_MAX_DIARIO", 1500)
        self.ventana_s, self._reloj, self._hoy = ventana_s, reloj, hoy
        self._clientes: dict[str, deque[float]] = defaultdict(deque)
        self._todos: deque[float] = deque()
        self._dia, self._n_dia = hoy(), 0
        self._lock = threading.Lock()

    def permitir(self, cliente: str) -> str | None:
        """None si puede preguntar; si no, el motivo."""
        with self._lock:
            ahora = self._reloj()
            if self._hoy() != self._dia:
                self._dia, self._n_dia = self._hoy(), 0
            for cola in (self._todos, self._clientes[cliente]):
                while cola and ahora - cola[0] > self.ventana_s:
                    cola.popleft()
            if self._n_dia >= self.diario:
                return "tope diario de preguntas"
            if len(self._todos) >= self.global_min:
                return "demasiadas preguntas por minuto en el servicio"
            if len(self._clientes[cliente]) >= self.por_cliente:
                return "demasiadas preguntas por minuto"
            self._todos.append(ahora)
            self._clientes[cliente].append(ahora)
            self._n_dia += 1
            return None


limitador = Limitador()
