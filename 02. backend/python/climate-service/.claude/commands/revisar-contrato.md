---
description: Pide al agente guardian-del-contrato que revise los cambios actuales
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git status:*), Bash(pytest:*)
---

Usa el agente `guardian-del-contrato` para revisar los cambios sin commitear y los commits de esta rama frente a `origin/develop`. Muéstrame su informe tal cual y, al final, lista lo que debo avisar a Jhonny (API Java) y a Sheila (app) antes del Pull Request. $ARGUMENTS
