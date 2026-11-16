#!/bin/sh
# Se ejecuta al arrancar el contenedor (carpeta /docker-entrypoint.d de la imagen de nginx).
# Si no hay certificado en /etc/nginx/certs, genera uno autofirmado PROVISIONAL para que nginx arranque
# y el sitio por IP en HTTP no se caiga. El certificado real (Let's Encrypt) lo copia el hook de certbot.
set -e

CERT_DIR="/etc/nginx/certs"
CN="${SSL_CERT_CN:-allpashift.crisaor.org}"

mkdir -p "$CERT_DIR"

if [ -s "$CERT_DIR/fullchain.pem" ] && [ -s "$CERT_DIR/privkey.pem" ]; then
  echo "[tls] Usando los certificados de $CERT_DIR"
  exit 0
fi

echo "[tls] No hay certificado: se genera uno autofirmado provisional para $CN"
echo "[tls] AVISO: con Cloudflare en Full (strict) el dominio dará error 526 hasta emitir el de Let's Encrypt"
openssl req -x509 -nodes -newkey rsa:2048 -days 90 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=$CN" \
  -addext "subjectAltName=DNS:$CN"
chmod 600 "$CERT_DIR/privkey.pem"
chmod 644 "$CERT_DIR/fullchain.pem"
