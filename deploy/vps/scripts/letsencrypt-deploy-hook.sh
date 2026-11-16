#!/usr/bin/env bash
# Hook de certbot: copia el certificado al volumen del frontend y recarga nginx.
# certbot lo ejecuta solo tras cada renovación (se instala en /etc/letsencrypt/renewal-hooks/deploy/).
set -euo pipefail

CERT_DEST="${CERT_DEST:-/opt/allpashift/certs/frontend}"
CONTENEDOR="${CONTENEDOR:-allpashift-frontend}"

if [[ -n "${RENEWED_LINEAGE:-}" ]]; then
  LIVE="$RENEWED_LINEAGE"
  DOMAIN="${RENEWED_LINEAGE##*/}"
else
  DOMAIN="${1:-allpashift.crisaor.org}"
  LIVE="/etc/letsencrypt/live/$DOMAIN"
fi

if [[ ! -f "$LIVE/fullchain.pem" || ! -f "$LIVE/privkey.pem" ]]; then
  echo "[letsencrypt-deploy] ERROR: no hay certificado en $LIVE" >&2
  exit 1
fi

mkdir -p "$CERT_DEST"
cp -f "$LIVE/fullchain.pem" "$CERT_DEST/fullchain.pem"
cp -f "$LIVE/privkey.pem" "$CERT_DEST/privkey.pem"
chmod 644 "$CERT_DEST/fullchain.pem"
chmod 600 "$CERT_DEST/privkey.pem"
echo "[letsencrypt-deploy] Certificado copiado a $CERT_DEST (dominio=$DOMAIN)"

if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -qx "$CONTENEDOR"; then
  docker exec "$CONTENEDOR" nginx -s reload
  echo "[letsencrypt-deploy] nginx recargado en $CONTENEDOR"
else
  echo "[letsencrypt-deploy] El contenedor $CONTENEDOR no está corriendo: se usará el certificado al desplegar el frontend"
fi
