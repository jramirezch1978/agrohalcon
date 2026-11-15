import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import calcular, mapa, punto, salud, suelo, validacion

app = FastAPI(
    title="AllpaShift – servicio de cálculos",
    description="Indicadores de riesgo climático con datos de la NASA. Reglas simples y explicables, sin IA.",
    version="0.1.0",
)

# En producción lo llama Java (servidor a servidor, sin CORS). Esto es para el modo híbrido de la
# app en desarrollo: Vite (localhost:5173 o la IP de la PC en la red local) y Capacitor.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost,https://localhost,capacitor://localhost"
    ).split(","),
    allow_origin_regex=r"http://(192\.168|10|172\.(1[6-9]|2\d|3[01]))(\.\d{1,3}){2,3}:5173",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(salud.router)
app.include_router(calcular.router)
app.include_router(mapa.router)
app.include_router(punto.router)
app.include_router(validacion.router)
app.include_router(suelo.router)
