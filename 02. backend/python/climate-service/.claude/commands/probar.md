---
description: Corre pruebas y lint del servicio y resume el estado en 5 líneas
allowed-tools: Bash(pytest:*), Bash(python -m pytest:*), Bash(ruff check:*), Read
---

Corre `pytest` y `ruff check .` en esta carpeta. Después resume en máximo 5 líneas: cuántas pruebas pasaron, cuáles fallaron (con la causa probable) y qué haría falta para arreglarlas. Si todo pasa, di cuántas pruebas hay por archivo. No modifiques código. $ARGUMENTS
