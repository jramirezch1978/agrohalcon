"""Capa de bases de datos de AgroShift.

Un solo esquema (schema.py) genera:
  * SQLite  -> data/agroshift.sqlite, para trabajar y probar en la PC de David sin Docker.
  * PostgreSQL -> db/postgres/*.sql, para el VPS de Jhonny (el contrato fija PostgreSQL).
El servicio FastAPI NO lee esta base (contrato): la usan los scripts, los análisis y el panel.
"""
