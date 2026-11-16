# Etapa 1: compilar Vue
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Etapa 2: servir con Nginx (proxy /api -> api-gateway)
FROM nginx:1.27-alpine
# openssl: para el certificado provisional si aún no hay uno de Let's Encrypt (ver 40-certificado-tls.sh)
RUN apk add --no-cache openssl
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY app-locations.inc /etc/nginx/conf.d/app-locations.inc
COPY 40-certificado-tls.sh /docker-entrypoint.d/40-certificado-tls.sh
RUN chmod +x /docker-entrypoint.d/40-certificado-tls.sh
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80 443