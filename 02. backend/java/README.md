# Microservicios Java (Java 17 + Spring Boot, Maven multi-módulo)

| Servicio | Puerto | Función |
|---|---|---|
| `api-gateway` | 8080 | Puerta de entrada única (Spring Cloud Gateway). `/api/agro/**` → agro-service · `/api/climate/**` → climate-service (Python) |
| `agro-service` | 8081 | Cultivos, calendario por quincena, comparador de rotaciones |

Compilar todo: `build.bat java` (o `mvn clean package` en esta carpeta).