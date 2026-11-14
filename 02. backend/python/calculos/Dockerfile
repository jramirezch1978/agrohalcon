# Servicio de cálculos de AgroShift (Sheila): FastAPI en el puerto 8001.
# Solo calcula y consulta la NASA (regla 3 del doc 29): no se conecta a PostgreSQL.
# Los datos pesados (GPM IMERG, MUR SST) ya vienen precalculados en data/precalculado/.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CACHE_DIR=/tmp/cache
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config ./config
COPY data/precalculado ./data/precalculado
COPY data/catalogo_ejemplo.json ./data/catalogo_ejemplo.json

RUN useradd --system --uid 10001 appuser
USER appuser

EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=3s --retries=3   CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/salud', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
