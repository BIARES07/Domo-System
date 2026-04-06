# Guía de Estudio y Referencia para el Pasante (Intern)

Este documento es una referencia sobre los retos técnicos que enfrentarás al conectarte al API Gateway "Hostil" de Sistema DOMO. Tu objetivo es construir un cliente robusto, tolerante a fallos y capaz de procesar datos ofuscados.

---

## 1. Proceso de Autenticación (El Handshake)

Tu cliente no puede acceder a los datos directamente. Debes implementar un flujo de autenticación dinámico en dos pasos:

### Paso 1: Obtener la Semilla
Debes realizar una petición `GET` no autenticada al nodo de entrada:
*   **Endpoint:** `GET /api/v1/init/`
*   **Respuesta:** Recibirás un JSON con una llave llamada `crypto_seed`. Guarda este valor en memoria, es fundamental para el siguiente paso.

### Paso 2: Generar Cabeceras (Headers) Criptográficas
Para acceder a los endpoints protegidos (`/intern/*`), cada una de tus peticiones HTTP debe incluir obligatoriamente dos cabeceras:

1.  **`X-Domo-Time`**: El *timestamp* actual en formato Unix (segundos desde 1970) como cadena de texto (String). *Nota: Si la petición tarda más de 30 segundos en llegar al servidor, será rechazada.*
2.  **`X-Domo-Token`**: Un hash criptográfico calculado usando el algoritmo **SHA256**.
    *   **Fórmula:** `SHA256(crypto_seed + X-Domo-Time)`
    *   **Formato esperado:** Cadena Hexadecimal.
3.  **`X-Domo-Session`**: El `session_id` devuelto por `GET /api/v1/init/`. Para acceso básico el sistema puede tolerar clientes legados, pero este identificador es el que permite protocolos avanzados como la rotación de sesión.

**📚 Temas a estudiar para la autenticación:**
*   Conceptos de APIs REST y Peticiones HTTP.
*   Manejo de Cabeceras (HTTP Headers) en tu lenguaje o librería HTTP (Axios, Fetch, Requests, etc.).
*   Criptografía básica: Funciones Hashing, específicamente implementación de **SHA256**.
*   Manejo de tiempos y conversiones a Unix Timestamp.
*   Mitigación de ataques de repetición (*Replay Attacks*).

---

## 2. Endpoints Disponibles (Intern API)

Todos los endpoints devuelven datos reales de operaciones espaciales. Deben ser consumidos utilizando el método `GET` y enviando las cabeceras de autenticación explicadas anteriormente.

*   🔭 **Clima Espacial:** `GET /api/v1/intern/weather`
    *   *Fuente:* NASA DONKI (Solar Flares).
*   ☄️ **Rastreo de Asteroides (NEOs):** `GET /api/v1/intern/neos`
    *   *Fuente:* NASA NeoWs.
*   🛰️ **Telemetría de Satélites:** `GET /api/v1/intern/satellites`
    *   *Fuente:* CelesTrak (Activos en órbita terrestre).
*   🚀 **Ventanas de Lanzamiento:** `GET /api/v1/intern/launches`
    *   *Fuente:* Feed operacional DOMO para misiones y countdowns de despliegue.
*   ⚠️ **Alertas de Conjunción:** `GET /api/v1/intern/conjunctions`
    *   *Fuente:* Feed operacional DOMO derivado de geometría orbital y telemetría de activos.
*   🌌 **Imagen Astronómica:** `GET /api/v1/intern/apod`
    *   *Fuente:* NASA APOD (Astronomy Picture of the Day).

---

## 3. Las Trampas del Game Master y Cómo Superarlas

El servidor actuará de forma hostil y errática de manera intencionada. Tu cliente debe estar programado a la defensiva para superar los siguientes obstáculos.

### Trampa Nivel 1: `json_mutation` (Mutación de Estructuras)
*   **Comportamiento:** Las respuestas JSON que normalmente esperarías llegarán con las claves (keys) alteradas. Se les añadirá el sufijo `_cruda` (ej: en lugar de `flrID`, llegará `flrID_cruda`). Esto romperá los modelos estrictos o tipados rígidos de tu frontend.
*   **Afecta a:** `/weather`, `/neos`, `/apod`, `/satellites`.
*   **📚 Temas a estudiar:**
    *   Programación defensiva.
    *   Acceso dinámico a propiedades de objetos/diccionarios.
    *   Mapeo, transformación y limpieza de datos (Data Parsing/Sanitization).
    *   Manejo de valores por defecto (Default fallbacks).

### Trampa Nivel 2: `random_failures` (Caos HTTP)
*   **Comportamiento:** Aleatoriamente, el servidor rechazará procesar tu petición y devolverá códigos de error como `500 Internal Server Error`, `429 Too Many Requests` o `503 Service Unavailable`.
*   **Afecta a:** Todos los endpoints `/intern/`.
*   **📚 Temas a estudiar:**
    *   Códigos de Estado HTTP y su significado.
    *   Manejo de Excepciones y control de errores (Try/Catch).
    *   **Implementación de algoritmos de "Retry"** (Reintentos automáticos).
    *   Patrones de resiliencia: **Exponential Backoff** (Esperar progresivamente más tiempo antes de cada reintento para no saturar al servidor).

### Trampa Nivel 2: `latency` (Degradación de Red)
*   **Comportamiento:** El servidor retendrá tu petición intencionalmente, tardando entre 1 y 5 segundos en responder.
*   **Afecta a:** Todos los endpoints `/intern/`.
*   **📚 Temas a estudiar:**
    *   Programación Asíncrona (`async/await`, Promesas, Futures).
    *   Configuración de *Timeouts* en clientes HTTP (evitar que la conexión se cierre prematuramente).
    *   **Diseño de Experiencia de Usuario (UX):** Implementación de estados de carga (Loading Spinners, Skeleton Screens) para evitar que la interfaz gráfica se congele mientras se esperan los datos.

### Trampa Avanzada: `seed_rotation` (Rotación de Sesión)
*   **Comportamiento:** Si una sesión autenticada permanece activa por más de una hora, las respuestas pasan a entregarse como un `payload_buffer` en Base64. El request puede seguir teniendo un timestamp fresco; lo que vence es la sesión, no la firma del request individual.
*   **Afecta a:** Cualquier endpoint `/intern/*` cuando la trampa esté activa.
*   **📚 Temas a estudiar:**
    *   Manejo de sesiones de corta vida.
    *   Renovación de handshake sin perder estado local.
    *   Decodificación Base64 y detección de modos de respuesta mixtos.

### Trampa Nivel 3: `binary_tle` (Empaquetado Binario)
*   **Comportamiento:** En lugar de devolver un cómodo texto JSON, el endpoint enviará un flujo de bytes crudos (`application/octet-stream`). Los datos están empaquetados como estructuras C, en modo *Little-Endian*. Cada satélite ocupa 20 bytes: un Entero sin signo de 4 bytes (Norad ID) seguido de 4 números decimales (Float) de 4 bytes cada uno.
*   **Afecta a:** Exclusivamente a `/satellites`.
*   **📚 Temas a estudiar:**
    *   Lectura de cabeceras HTTP de respuesta (especialmente `Content-Type`).
    *   Procesamiento de datos binarios (Buffers, Streams).
    *   Decodificación de memoria según el lenguaje: `DataView` y `ArrayBuffer` en JavaScript, o la librería `struct` en Python.
    *   Conceptos de arquitecturas de memoria: *Little-Endian* vs *Big-Endian*.
    *   Tipos de datos de bajo nivel (Unsigned Int de 32 bits, Float de 32 bits).

### Trampa Avanzada: `launch_window_fragmentation` (Fragmentación de Ventanas de Lanzamiento)
*   **Comportamiento:** El endpoint `/launches` deja de devolver una lista plana. En su lugar responde con un paquete `manifest` y cada misión mueve sus horarios a un `window_packet`, mientras que `status` y `countdown` llegan fusionados en `launch_vector`.
*   **Afecta a:** `/launches`.
*   **📚 Temas a estudiar:**
    *   Normalización de payloads heterogéneos.
    *   Adaptadores de DTOs con soporte para estructuras anidadas.
    *   Parsing de strings compuestos y compatibilidad hacia atrás.

### Trampa Avanzada: `conjunction_signal_scramble` (Señal de Conjunción Reordenada)
*   **Comportamiento:** El endpoint `/conjunctions` responde con un objeto `alerts`, reordena eventos por tiempo de aproximación y encapsula las métricas cinemáticas dentro de `geometry`. El riesgo puede venir codificado como `threat_band` en lugar de un número directo.
*   **Afecta a:** `/conjunctions`.
*   **📚 Temas a estudiar:**
    *   Reordenamiento local de colecciones según criticidad.
    *   Extracción de métricas numéricas desde strings estructurados.
    *   Lectura defensiva de objetos anidados.
