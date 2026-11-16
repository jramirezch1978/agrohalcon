# HTTPS con Cloudflare para AllpaShift

Dominio: **https://allpashift.crisaor.org** (zona `crisaor.org`, DNS en Cloudflare).
Servidor: VPS Hetzner, IP fija `2.29.101.199`, puertos **80 y 443 libres**.

> Adaptado de `deploy/cronos/CLOUDFLARE.md` del repositorio SIGRE. Allí el 443 del router está ocupado y se usa el puerto 8080 con la nube gris;
> aquí el 443 está libre, la IP es fija (no hace falta CNAME ni DDNS) y se usa la **nube naranja** de Cloudflare.

## Cómo queda

| Acceso | Qué pasa |
|--------|----------|
| `http://2.29.101.199` | Sigue igual, por **HTTP y sin redirección**. Lo usan el APK y la app iOS ya publicados |
| `http://allpashift.crisaor.org` | Redirige a HTTPS |
| `https://allpashift.crisaor.org` | HTTPS con certificado de Let's Encrypt en el servidor y Cloudflare por delante |

Cloudflare (nube naranja) aporta compresión y caché de los archivos `/assets`, lo que ayuda a la lentitud al cargar la app.

## 1. Cloudflare (panel)

1. **DNS → Records → Add record**: tipo `A`, nombre `allpashift`, contenido `2.29.101.199`, **Proxy status: Proxied (nube naranja)**.
2. **SSL/TLS → Overview**: modo **Full (strict)**.
   - No usar *Flexible*: Cloudflare hablaría en HTTP con el servidor y el redirect de nginx provocaría un bucle (`ERR_TOO_MANY_REDIRECTS`).
3. **API token**: https://dash.cloudflare.com/profile/api-tokens → *Create Token* → plantilla **Edit zone DNS** → zona `crisaor.org`. Se puede reutilizar el token de SIGRE si ya existe. Guardarlo, solo se muestra una vez.

## 2. Firewall de Hetzner

Abrir el **443/tcp** (en el Cloud Firewall del panel de Hetzner y, si se usa, en `ufw`):

```bash
ufw allow 443/tcp
```

## 3. Emitir el certificado (una sola vez)

Desde Windows, en la raíz del repo, subir los scripts:

```bat
scp deploy\vps\scripts\setup-letsencrypt-cloudflare.sh deploy\vps\scripts\letsencrypt-deploy-hook.sh root@2.29.101.199:/tmp/
```

Guardar el token en el servidor sin dejarlo en el historial (pegar el token y cerrar con Ctrl+D):

```bat
ssh root@2.29.101.199 "umask 077; cat > /root/cloudflare-token.txt"
```

Emitir el certificado y dejar la renovación automática:

```bat
ssh -t root@2.29.101.199 "CLOUDFLARE_API_TOKEN_FILE=/root/cloudflare-token.txt bash /tmp/setup-letsencrypt-cloudflare.sh <EMAIL>"
```

El script instala certbot, emite el certificado de `allpashift.crisaor.org` y lo copia a `/opt/allpashift/certs/frontend`
(`fullchain.pem` y `privkey.pem`). La renovación queda en el timer de certbot (cada ~60 días) y el hook recarga nginx solo.

Comprobar la renovación en seco:

```bash
certbot renew --dry-run
```

## 4. Desplegar el frontend

Con este cambio el frontend publica también el **443** y monta la carpeta de certificados.

```bat
deploy.bat frontend --force
```

Si el frontend se despliega **antes** de emitir el certificado, no se cae: genera uno autofirmado provisional y el sitio por IP sigue funcionando.
El dominio dará error 526 de Cloudflare hasta que se emita el certificado real (paso 3).

## 5. Verificar

```bash
curl -I https://allpashift.crisaor.org/
```

```bash
curl -I http://2.29.101.199/
```

- El primero debe responder `200` con `Strict-Transport-Security`; en el navegador, sin advertencia de "no seguro".
- El segundo debe responder `200` por HTTP **sin** redirigir (si redirige, se rompen el APK y el iOS).

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Error **526** | Certificado inválido en el servidor (el provisional) | Emitir el de Let's Encrypt (paso 3) |
| Error **521** | Cloudflare no llega al servidor | Abrir el 443 (paso 2) y comprobar que `allpashift-frontend` esté corriendo |
| `ERR_TOO_MANY_REDIRECTS` | Cloudflare en *Flexible* | Cambiar a **Full (strict)** |
| El certificado no se renueva | Token vencido o sin permiso DNS Edit | Crear otro token y repetir el paso 3 |

## Lo que viene después (no incluido aquí)

- **App móvil:** cuando el dominio funcione, apuntar `VITE_API_URL` de `03. frontend/.env.mobile` a `https://allpashift.crisaor.org`, quitar `allowMixedContent` de `capacitor.config.ts` y publicar un APK/iOS nuevo. Mientras tanto, la IP por HTTP mantiene funcionando los ya publicados.
- **PWA / uso sin conexión:** el service worker solo se puede registrar con HTTPS; queda como tarea del frontend una vez que el dominio esté activo.
- **CORS:** no hace falta tocarlo; el gateway ya acepta cualquier origen y el navegador llama a `/api` en el mismo dominio.
