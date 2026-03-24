# Manual de Protocolos de Emergencia - Sistema DOMO

Este documento detalla los desafíos técnicos presentes en el Gateway de DOMO y las estrategias de ingeniería requeridas para su resolución.

## 1. Protocolo de Autenticación (Handshake)

Para cualquier petición a la API, el cliente debe implementar la firma criptográfica dinámica.

**Procedimiento:**
1. Obtener `crypto_seed` desde el endpoint `/api/v1/init`.
2. Generar un `X-Domo-Time` (Unix Timestamp actual).
3. Concatenar `seed + timestamp` como string.
4. Calcular el hash **SHA256** de esa concatenación.
5. Enviar ambos valores en los headers `X-Domo-Time` y `X-Domo-Token`.

---

## 2. Guía de Resolución de Anomalías (Trampas)

### Nivel 1: Mutación de Esquema (JSON Mutation)
*   **Anomalía:** Las llaves del JSON aparecen con sufijos como `_cruda`.
*   **Resolución:** Implementar un **Mapping Adapter**. El cliente no debe confiar en llaves fijas, sino buscar mediante un regex o un fallback: `data.velocidad || data.velocidad_cruda`.

### Nivel 1+: Deriva de Tipos (Schema Drift)
*   **Anomalía:** Valores que deberían ser números llegan como strings con unidades (ej: `"12.5 km/s"`).
*   **Resolución:** Crear una función de **Sanitización de Datos**. Usar casting dinámico: `parseFloat(valor.split(' ')[0])`.

### Nivel 2: Inestabilidad de Red (HTTP Chaos)
*   **Anomalía:** Errores aleatorios 500, 429 o 503.
*   **Resolución:** Implementar **Políticas de Reintento (Retries)** con **Exponential Backoff**. No dar por fallida la operación hasta al menos 3 intentos fallidos.

### Nivel 2: Degradación de Performance (Latency)
*   **Anomalía:** Peticiones que tardan más de 5 segundos.
*   **Resolución:** Configurar **Timeouts** adecuados en el cliente y mostrar estados de carga (*Loading states*) en la UI para mejorar la experiencia de usuario a pesar del lag.

### Nivel 2+: Paginación Inconsistente
*   **Anomalía:** Solo se reciben 3 elementos a pesar de que hay cientos disponibles.
*   **Resolución:** Inspeccionar los metadatos de la respuesta. Si existe un campo `next_range`, el cliente debe enviar el header `X-Domo-Range: items=X-Y` para solicitar el siguiente bloque de datos.

### Nivel 2+: Rotación de Semilla (Seed Rotation)
*   **Anomalía:** Los datos llegan como un buffer Base64 en el campo `payload_buffer`.
*   **Resolución:** Detección de tipo de respuesta. Si el status es `SESSION_ENCRYPTED_UPGRADE_REQUIRED`, el cliente debe decodificar el Base64 y realizar un nuevo Handshake para refrescar la semilla.

### Nivel 3: Protocolo Binario (Binary TLE)
*   **Anomalía:** El `Content-Type` cambia a `application/octet-stream`.
*   **Resolución:** Buffer Parsing. Utilizar `DataView` en JS o `struct` en Python para leer los bytes según el esquema: `[Uint32 (NORAD ID), Float32 x 4 (Telemetría)]`.

### Nivel 3: HATEOAS Dinámico
*   **Anomalía:** Las URLs hardcodeadas dejan de funcionar cada 24 horas.
*   **Resolución:** **Service Discovery**. El cliente nunca debe tener URLs fijas (excepto `/init`). Debe consumir el mapa de `links` de la respuesta inicial cada vez que arranca la sesión.

---

# Estrategia de Gestión del Pasante (4 Meses)

El objetivo es que el pasante desarrolle resiliencia y habilidades de arquitectura. La clave es el **"Goteo de Caos"**.

## Calendario de Despliegue

| Mes | Enfoque Técnico | Trampas a Activar | Qué Revelar |
| :--- | :--- | :--- | :--- |
| **1** | Conectividad Básica | Latency (Baja), JSON Mutation | "El sistema es antiguo y las llaves son inconsistentes". |
| **2** | Robustez y Errores | HTTP Chaos (Prob: 0.2), Schema Drift | "Estamos migrando sensores, los tipos de datos pueden variar". |
| **3** | Optimización y Seguridad | Inconsistent Paging, Seed Rotation | "Se activó el protocolo de ahorro de banda y rotación de llaves". |
| **4** | Bajo Nivel y Dinamismo | Binary TLE, Dynamic HATEOAS | "Protocolo militar activado. Solo comunicación binaria directa". |

## Metodología de Mentoría

### Qué NO revelar nunca:
*   **La existencia del Dashboard de GM:** El pasante nunca debe saber que tú tienes "interruptores" para causarle problemas. Para él, el sistema es simplemente "inestable por naturaleza".
*   **Que el caos es artificial:** Si pregunta por qué falla, responde: *"Es un sistema crítico procesando datos de espacio profundo; las interferencias y la deuda técnica son normales"*.

### Cuándo y cómo ayudar:
1.  **Regla de las 24 horas:** Si el pasante se bloquea con una trampa, deja que investigue solo un día entero. La frustración controlada es parte del aprendizaje.
2.  **Pistas de "Documentación Vieja":** Si sigue bloqueado, entrégale una "nota técnica recuperada" (puedes copiar fragmentos de la sección 2 de este MD) sugiriendo que "otros ingenieros usaron Normalizadores de Datos".
3.  **Refuerzo Positivo:** Cuando logre superar una trampa (ej. cuando implemente Retries y el sistema deje de fallar en su UI), felicítalo por su **"Arquitectura Resiliente"**.

## Criterio de Éxito
Al final de los 4 meses, el pasante no solo debe tener un dashboard que funcione, sino un **SDK (Software Development Kit)** propio que sea capaz de manejar cualquier API inestable del mundo real.
