# Rutas de la aplicación. Las comparten el servidor HTTP (acceso por IP) y el servidor HTTPS (dominio).

# API: todo pasa por el api-gateway
location /api/ {
    limit_req zone=api burst=20 nodelay;   # ráfagas de la app (varias pantallas a la vez) pasan; abuso sostenido -> 429
    proxy_pass http://api-gateway:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

# Proxy a ERDDAP de NOAA (MUR SST de NASA JPL): no permite CORS desde el navegador
location /nasa/erddap/ {
    limit_req zone=erddap burst=5 nodelay;
    proxy_pass https://coastwatch.pfeg.noaa.gov/erddap/;
    proxy_set_header Host coastwatch.pfeg.noaa.gov;
    proxy_ssl_server_name on;
    proxy_read_timeout 30s;
}

# Archivos con hash (Vite): se guardan un año; si falta uno (versión vieja en caché) da 404, nunca index.html
location /assets/ {
    try_files $uri =404;
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header Strict-Transport-Security $hsts always;
}

# SPA: rutas del frontend. index.html nunca se guarda en caché, así cada despliegue se ve al instante
location / {
    try_files $uri $uri/ /index.html;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Strict-Transport-Security $hsts always;
}
