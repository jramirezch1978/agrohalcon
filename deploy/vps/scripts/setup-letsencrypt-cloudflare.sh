#!/usr/bin/env bash
# Emite el certificado Let's Encrypt de allpashift.crisaor.org (DNS-01 por la API de Cloudflare),
# lo copia al volumen del frontend y deja la renovación automática.
#
# Requisitos:
#   1. Token API de Cloudflare con permiso Zone > DNS > Edit en la zona crisaor.org
#      https://dash.cloudflare.com/profile/api-tokens -> Create Token -> plantilla "Edit zone DNS"
#   2. Ejecutar en el VPS como root, junto a letsencrypt-deploy-hook.sh (misma carpeta)
#
# Uso (el token en archivo evita que quede en el historial de la consola):
#   CLOUDFLARE_API_TOKEN_FILE=/root/cloudflare-token.txt bash setup-letsencrypt-cloudflare.sh jramirez@npssac.com.pe
# o con el token como segundo argumento:
#   bash setup-letsencrypt-cloudflare.sh jramirez@npssac.com.pe <TOKEN>
set -euo pipefail

EMAIL="${1:-}"
TOKEN_ARG="${2:-}"
DOMAIN="${SSL_CERT_CN:-allpashift.crisaor.org}"
CERT_DEST="${CERT_DEST:-/opt/allpashift/certs/frontend}"
CREDS="/etc/letsencrypt/cloudflare.ini"
HOOK_SRC="$(cd "$(dirname "$0")" && pwd)/letsencrypt-deploy-hook.sh"
HOOK_DST="/etc/letsencrypt/renewal-hooks/deploy/allpashift-frontend.sh"

if [[ -z "$EMAIL" ]]; then
  echo "Uso: $0 <email-letsencrypt> [token-cloudflare]"
  exit 1
fi
if [[ ! -f "$HOOK_SRC" ]]; then
  echo "ERROR: falta letsencrypt-deploy-hook.sh junto a este script"
  exit 1
fi

TOKEN=""
if [[ -n "${CLOUDFLARE_API_TOKEN_FILE:-}" && -f "$CLOUDFLARE_API_TOKEN_FILE" ]]; then
  TOKEN="$(tr -d '[:space:]' < "$CLOUDFLARE_API_TOKEN_FILE")"
elif [[ -n "$TOKEN_ARG" ]]; then
  TOKEN="$TOKEN_ARG"
elif [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  TOKEN="$CLOUDFLARE_API_TOKEN"
fi
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: falta el token de Cloudflare (CLOUDFLARE_API_TOKEN_FILE, segundo argumento o CLOUDFLARE_API_TOKEN)"
  exit 1
fi

echo "==> Instalando certbot con el plugin de Cloudflare..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y certbot python3-certbot-dns-cloudflare
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y certbot python3-certbot-dns-cloudflare
else
  echo "ERROR: no encuentro apt-get ni dnf; instala certbot y python3-certbot-dns-cloudflare a mano"
  exit 1
fi

echo "==> Guardando las credenciales de Cloudflare (solo root) en $CREDS"
umask 077
mkdir -p "$(dirname "$CREDS")"
cat > "$CREDS" <<EOF
# Generado por setup-letsencrypt-cloudflare.sh. No versionar.
dns_cloudflare_api_token = $TOKEN
EOF
chmod 600 "$CREDS"

echo "==> Instalando el hook de renovación en $HOOK_DST"
mkdir -p "$(dirname "$HOOK_DST")"
cp -f "$HOOK_SRC" "$HOOK_DST"
chmod 755 "$HOOK_DST"

echo "==> Emitiendo el certificado de $DOMAIN (DNS-01 por Cloudflare)..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials "$CREDS" \
  --dns-cloudflare-propagation-seconds 60 \
  -d "$DOMAIN" \
  --cert-name "$DOMAIN" \
  --agree-tos -m "$EMAIL" --no-eff-email \
  --non-interactive

echo "==> Copiando el certificado al volumen del frontend ($CERT_DEST)"
CERT_DEST="$CERT_DEST" bash "$HOOK_DST" "$DOMAIN"

echo "==> Activando la renovación automática..."
if systemctl list-unit-files certbot.timer 2>/dev/null | grep -q certbot.timer; then
  systemctl enable --now certbot.timer
elif systemctl list-unit-files certbot-renew.timer 2>/dev/null | grep -q certbot-renew.timer; then
  systemctl enable --now certbot-renew.timer
else
  echo "    (sin timer de systemd) se agrega un cron diario"
  cat > /etc/cron.d/certbot-allpashift <<'CRON'
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
0 3 * * * root certbot renew --quiet
CRON
  chmod 644 /etc/cron.d/certbot-allpashift
fi

echo ""
echo "Listo. Prueba la renovación en seco con:  certbot renew --dry-run"
echo "Prueba el sitio con:                      curl -I https://$DOMAIN/"
