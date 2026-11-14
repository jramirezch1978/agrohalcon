# Servidores para el despliegue de AgroHalcón (investigado el 2026-11-13)

Necesitamos: **API Java 17 (Spring Boot)** + **servicio Python (FastAPI)** + **web estática (Vue)**, accesibles por enlace público **al menos hasta el 19 nov** (jurado local) e idealmente hasta enero 2027 (etapa global).

## VPS gratuitos

| Proveedor | Qué da gratis | ¿Expira? | Sirve para nosotros | Notas |
|---|---|---|---|---|
| ⭐ **Oracle Cloud Always Free** | VM ARM Ampere A1 (doc. 2026: 2 OCPU y 12 GB RAM; guías antiguas dicen 4 OCPU / 24 GB) + 2 VM AMD micro | No | ✅ **Sí: corre Java + Python + Nginx en una sola VM** | Pide tarjeta para verificación · a veces "sin capacidad" en la región · elegir región **São Paulo o Santiago** |
| Google Cloud e2-micro | 1 VM, 1 GB RAM, 30 GB disco, 1 GB de salida/mes, solo regiones de EE. UU. | No | 🟡 Justo: 1 GB RAM no alcanza para Java + Python juntos | Pide tarjeta |
| AWS | Ya no da t2.micro gratis 12 meses a cuentas nuevas; créditos promocionales | Sí | 🟡 Solo con créditos | Pide tarjeta |
| Azure | US$200 de crédito por 30 días + B1s 12 meses | Sí | ✅ Alcanza para el hackathon | Pide tarjeta · **Azure for Students: US$100 sin tarjeta** con correo universitario (Sheila o Alejandro) |

## Recomendación

| Opción | Arquitectura | Costo |
|---|---|---|
| **A (recomendada)** | **Oracle Always Free** (VM ARM): API Java + servicio Python + Nginx · web en **Azure Static Web Apps** o en el mismo Nginx | US$0 permanente |
| **B (respaldo rápido)** | **Azure** (tu experiencia): App Service Java + App Service Python + Static Web Apps, con crédito gratuito o Azure for Students | US$0 durante el crédito |

⚠️ Crear la cuenta lo hace el titular (Jhonny) con sus datos y tarjeta; no se comparte la tarjeta ni contraseñas.

## VPS de pago barato (decisión 2026-11-13: todo con Docker + PostgreSQL)

**Consumo estimado con Docker:** api-gateway (~400 MB) + agro-service (~450 MB) + climate-service Python (~250 MB) + PostgreSQL (~250 MB) + Nginx con el frontend (~30 MB) ≈ **1,5–2 GB** → mínimo **4 GB de RAM**, ideal 8 GB.
**Tiempo de uso:** del 14 nov 2026 a ene 2027 (~2,5 meses) → conviene **pago por hora o mensual**, no prepago de 2 años.

| Proveedor | Plan | Precio aprox. | Facturación | Ubicación | Comentario |
|---|---|---|---|---|---|
| ⭐ **Hetzner** | CX22/CX23: 2 vCPU, 4 GB, 40 GB NVMe | ~US$5–6,5 / mes | **Por hora** | EE. UU. (Ashburn, Hillsboro), Europa | El más barato para 4 GB, se cancela cuando quieras |
| **Contabo** | Cloud VPS S: 8 GB RAM | ~US$7 / mes | Mensual (puede haber tarifa de alta) | EE. UU., Europa, Asia | Más RAM por dólar; disco y red más lentos |
| **Hostinger** | KVM 2: 2 vCPU, 8 GB, 100 GB NVMe, 8 TB | ~US$8,8–9 / mes **con prepago de 24 meses** (renueva a ~US$15) | Prepago largo para el precio bajo | EE. UU., Brasil (confirmar si São Paulo aplica a VPS) | Muy buen hardware, pero el precio barato obliga a pagar 2 años |
| **Clouding.io** | 2 vCPU, 4 GB, 40 GB | ~€14 / mes (≈ €0,0193 / hora) | **Por hora** | España (Barcelona) | Simple y en español, pero más caro y lejos de Perú |
| Vultr / DigitalOcean | 4 GB | ~US$20–24 / mes | Por hora | Vultr tiene São Paulo y Santiago | Más caros |

**Recomendación:** **Hetzner CX22/CX23 (4 GB, pago por hora, región EE. UU.)** → ~US$15 por todo el periodo del concurso. Si se quiere más holgura: **Contabo 8 GB**. **Hostinger** solo conviene si se va a seguir usando el servidor después del hackathon.

## Servidor contratado (2026-11-14)

- **Hetzner CPX32** (4 vCPU AMD, 8 GB RAM, 160 GB) · Helsinki · Rocky Linux 9.8 · nombre `agrohalcon-vps` · IP pública `2.29.101.199` · ~US$36/mes por hora.
- Docker 29.9.3 + Compose v5.7.1 · contexto Docker `agrohalcon-vps` (ssh://root@2.29.101.199) · firewall Hetzner aplicado.
- En línea: http://2.29.101.199 (web), `/api/agro/health`, `/api/climate/health`.

## Pendiente: HTTPS con Cloudflare (decisión de Jhonny)

1. Conseguir un dominio (Cloudflare no regala dominios: comprarlo en Cloudflare Registrar ~US$10/año o en otro registrador y apuntar los DNS a Cloudflare).
2. En Cloudflare: registro **A** `agrohalcon.<dominio>` → `2.29.101.199` con **proxy activado (nube naranja)**.
3. SSL/TLS: modo **Full** con certificado *Origin* de Cloudflare instalado en el Nginx del frontend (o **Flexible** como solución rápida para la demo).
4. Firewall Hetzner: dejar 80/443 abiertos (idealmente solo a los rangos IP de Cloudflare) y 22 para el despliegue.
5. Actualizar `05. mobile/capacitor.config.json` → `https://agrohalcon.<dominio>` y quitar `cleartext` / `usesCleartextTraffic`.
6. Alternativa sin abrir puertos: **Cloudflare Tunnel** (`cloudflared` en el VPS).

## Fuentes
- [Oracle Cloud Always Free Tier Cut 2026](https://braindetox.kr/en/posts/oracle_always_free_tier_reduced_2026.html)
- [Free VPS vs. Cheap VPS: The Whole Truth About 2026 Free Tiers](https://valebyte.com/en/blog/free-vps-vs_-cheap-vps-the-whole-truth-about-2026-free-tiers/)
- [How to Get a Free Cloud VPS Forever (Oracle, Google Cloud, AWS)](https://cpanelfree.com/blog/?p=1269)
- [Free VPS guide (verificado jun 2026)](https://klymentiev.com/blog/free-vps)
- [Hostinger VPS pricing (valebyte)](https://valebyte.com/en/providers/hostinger/) · [KVM 2 by Hostinger (VPSBenchmarks)](https://www.vpsbenchmarks.com/hosters/hostinger/plans/kvm-2)
- [Clouding.io 4GB 2 cores (VPSBenchmarks)](https://www.vpsbenchmarks.com/hosters/clouding_io/plans/4gb-2cores) · [Clouding 4 GB en WHTop](https://www.whtop.com/plans/clouding.io/90395)
- [VPS Price Tracker agosto 2026 (Findstack)](https://findstack.com/resources/vps-price-tracker) · [Hostinger vs Contabo vs Hetzner 2026](https://valebyte.com/en/blog/hostinger-vs-contabo-vs-hetzner-budget-vps-in-2026/)
