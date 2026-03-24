# Sistema DOMO: Desglose de Tareas (Fase 3 - Task SDD)

Este documento contiene el *Backlog* técnico del proyecto. Las tareas están diseñadas para ser atómicas, secuenciales e implementables directamente en código.

## Épica 1: Infraestructura y Core del Proyecto
**Objetivo:** Levantar el esqueleto de la aplicación, dependencias y conexiones base.

* **TSK-1.1: Inicialización del Proyecto FastAPI**
    * **Descripción:** Crear la estructura de carpetas (routers, services, core, db) y el archivo `main.py` con la instancia base de FastAPI.
    * **Criterios de Aceptación:** El servidor levanta en `localhost:8000` y expone la ruta `/docs` (Swagger) por defecto.
* **TSK-1.2: Configuración de Conexiones (SQLite y Redis)**
    * **Descripción:** Configurar SQLAlchemy (o `sqlite3` nativo) para la conexión a disco y `redis-py` asíncrono para la conexión en memoria.
    * **Criterios de Aceptación:** FastAPI se conecta a `domo_metrics.db` al iniciar y lanza un ping exitoso a Redis.

## Épica 2: Capa de Acceso a Datos (CRUD)
**Objetivo:** Materializar las tablas definidas en el Plan.

* **TSK-2.1: Modelado de Tablas SQLite**
    * **Descripción:** Crear los modelos/scripts SQL para las tablas `trainee_metrics` (métricas de uso) y `chaos_config` (estado de las trampas).
    * **Criterios de Aceptación:** Se pueden insertar y leer registros de prueba en ambas tablas mediante un script de validación.
* **TSK-2.2: Funciones CRUD de Interfaz**
    * **Descripción:** Escribir las funciones Python (ej. `log_metric()`, `get_active_traps()`) que encapsulan los queries SQL.
    * **Criterios de Aceptación:** Las funciones manejan excepciones de base de datos y retornan diccionarios limpios o Pydantic models.

## Épica 3: Servicios de Extracción de Datos (Data Fetchers)
**Objetivo:** Consumir las APIs externas de forma asíncrona.

* **TSK-3.1: Cliente Asíncrono NASA (DONKI, NeoWs, APOD)**
    * **Descripción:** Crear un servicio con `httpx.AsyncClient` para consultar los endpoints de la NASA, manejando los tokens de acceso y *timeouts*.
    * **Criterios de Aceptación:** Funciones independientes retornan los JSON puros de la NASA sin bloquear el *Event Loop*.
* **TSK-3.2: Cliente y Parser CelesTrak (TLE)**
    * **Descripción:** Extraer el archivo de texto plano de CelesTrak de satélites activos y parsear las líneas TLE a un formato estructurado (diccionario/lista).
    * **Criterios de Aceptación:** El parser extrae correctamente el NORAD ID y los parámetros orbitales de cada bloque de 3 líneas.

## Épica 4: Gamificación y Trampas (El Game Master)
**Objetivo:** Programar el "caos" y la seguridad del sistema.

* **TSK-4.1: Algoritmo de Empaquetado Binario**
    * **Descripción:** Crear una función pura usando `struct` que tome los datos de un satélite (lat, lon, alt, vel) y devuelva un `bytes` object crudo.
    * **Criterios de Aceptación:** Una función de test puede desempaquetar los bytes y obtener los mismos flotantes originales.
* **TSK-4.2: Algoritmo de Mutación JSON (Nivel 1)**
    * **Descripción:** Función recursiva que recibe un diccionario y altera sus claves agregando sufijos o cambiándolas según un mapa de mutación predefinido.
    * **Criterios de Aceptación:** `{ "velocidad": 100 }` muta a `{ "vel_cruda": 100 }` de forma determinista.
* **TSK-4.3: Middleware de Autenticación Criptográfica**
    * **Descripción:** Middleware HTTP de FastAPI que extrae los headers `X-Domo-Token`, `X-Domo-Time`, recalcula el SHA256 con la semilla secreta y valida.
    * **Criterios de Aceptación:** Peticiones sin el hash correcto o con un timestamp muy viejo (replay attack) retornan `401 Unauthorized`.
* **TSK-4.4: Middleware de Caos y Rate Limit**
    * **Descripción:** Middleware HTTP que lee la config de SQLite/Redis. Si el caos está activo, inyecta `asyncio.sleep()` aleatorios o retorna `500/429/503`.
    * **Criterios de Aceptación:** La tasa de inyección de errores coincide con el porcentaje de severidad configurado en la base de datos.

## Épica 5: Enrutadores (Endpoints)
**Objetivo:** Exponer la API hacia el exterior.

* **TSK-5.1: Nodo de Entrada y Pistas (`/api/v1/init`)**
    * **Descripción:** Endpoint público que entrega el token base, la semilla criptográfica y el HATEOAS inicial.
    * **Criterios de Aceptación:** Retorna JSON con token válido y expira en Redis tras un tiempo establecido.
* **TSK-5.2: Enrutador Fragmentado del Pasante**
    * **Descripción:** Programar las rutas definidas en el *Specify* (Clima, NEOs, APOD, Satélites) aplicando los middlewares y ensamblando la data de los *Data Fetchers*.
    * **Criterios de Aceptación:** Todos los endpoints responden correctamente a las peticiones firmadas. El endpoint TLE retorna el *buffer* binario si la trampa Nivel 3 está activa.
* **TSK-5.3: Enrutador del Centro de Comando (Admin)**
    * **Descripción:** Endpoints internos (o websockets) sin trampas que proveen toda la data consolidada para el panel de administración.
    * **Criterios de Aceptación:** Devuelve payloads ricos y completos, ignorando las reglas del Middleware de Caos.

## Épica 6: Centro de Comando (Frontend Admin)
**Objetivo:** Construir la interfaz inmersiva de monitoreo.

* **TSK-6.1: Esqueleto UI y Panel de Control de Trampas**
    * **Descripción:** Maquetación HTML/CSS pura y lógica JS para activar/desactivar los *toggles* en la base de datos mediante fetch al Gateway.
    * **Criterios de Aceptación:** Interfaz responsiva; cambiar un switch en la UI actualiza el `chaos_config` en SQLite instantáneamente.
* **TSK-6.2: Módulo Clima Espacial y APOD**
    * **Descripción:** Integración JS para pintar la línea de tiempo de llamaradas y el carrusel de imágenes astronómicas.
* **TSK-6.3: Radares Tácticos (Canvas API)**
    * **Descripción:** Uso de `<canvas>` y JS Vanilla para dibujar el radar 2D polar de NEOs y mapear la telemetría de los satélites en tiempo real.
    * **Criterios de Aceptación:** Renderizado a 60fps constantes sin fugas de memoria (*memory leaks*) al actualizar las posiciones.