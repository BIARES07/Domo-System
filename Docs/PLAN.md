# Sistema DOMO: Documento de Diseño Arquitectónico (Fase 2 - Plan SDD)

Este documento establece las normativas de diseño de software para el API Gateway (Backend) del Sistema DOMO, priorizando la mantenibilidad, el determinismo en la evaluación del pasante y evitando la sobreingeniería.

## Índice

1. [Topología del Sistema (Modelo C4)](#1-topología-del-sistema-modelo-c4)
   - [Diagrama de Contexto (Nivel 1)](./docs/diagramas/c4_nivel1_contexto.md)
   - [Diagrama de Contenedores (Nivel 2)](./docs/diagramas/c4_nivel2_contenedores.md)
   - [Diagrama de Componentes (Gateway Interno - Nivel 3)](./docs/diagramas/c4_nivel3_componentes.md)
2. [Tipo de Arquitectura de Software](#2-tipo-de-arquitectura-de-software)
3. [Paradigmas de Programación](#3-paradigmas-de-programación)
4. [Patrones de Diseño Tácticos](#4-patrones-de-diseño-tácticos)

---

## 1. Topología del Sistema (Modelo C4)
La estructura visual de esta arquitectura está fundamentada en los diagramas del Modelo C4 desarrollados para el proyecto. Los archivos fuente y renders se encuentran en el directorio `/docs/diagramas/` del repositorio.

* **Contexto (Nivel 1):** Muestra la interacción de alto nivel entre el Game Master, el Pasante, DOMO y las fuentes de datos espaciales. *(Ver: [c4_nivel1_contexto.md](./docs/diagramas/c4_nivel1_contexto.md))*
* **Contenedores (Nivel 2):** Define las unidades de despliegue principales: Admin UI (Vanilla JS), API Gateway (FastAPI), Caché (Redis) y Persistencia (SQLite). *(Ver: [c4_nivel2_contenedores.md](./docs/diagramas/c4_nivel2_contenedores.md))*
* **Componentes (Nivel 3):** Desglosa la anatomía interna de FastAPI, detallando el flujo de intercepción desde los middlewares hasta la capa de acceso a datos. *(Ver: [c4_nivel3_componentes.md](./docs/diagramas/c4_nivel3_componentes.md))*

## 2. Tipo de Arquitectura de Software
Se implementará una **Arquitectura en 3 Capas (Layered Architecture)** adaptada al ecosistema de FastAPI. Se descarta el enfoque de Arquitectura Hexagonal estricta (Puertos y Adaptadores) por ser innecesariamente complejo para el alcance del proyecto, dado que la elección de SQLite como base de datos persistente es definitiva. 

El sistema aislará las responsabilidades en las siguientes capas:
* **Capa de Presentación (Routers):** Exclusiva para la definición de endpoints (`/api/v1/...`). Su única labor es recibir la petición HTTP, validar el esquema de entrada (usando Pydantic) y retornar la respuesta. No contiene lógica de negocio.
* **Capa de Lógica de Negocio (Services):** Contiene el núcleo del sistema. Aquí residen los clientes HTTP para consumir las APIs externas (NASA, CelesTrak), así como los algoritmos del "Game Master" (empaquetado binario, ofuscación y cálculo de penalizaciones).
* **Capa de Acceso a Datos (CRUD):** Abstrae las operaciones de lectura y escritura hacia SQLite y Redis.

## 3. Paradigmas de Programación
El código base operará bajo un enfoque híbrido, dictado por la naturaleza de entrada/salida (I/O) del sistema y la necesidad de determinismo en las trampas de evaluación:

* **Paradigma Asíncrono / Reactivo (Core):** Dado que el Gateway es una aplicación 100% *I/O bound*, todas las interacciones con APIs de terceros y la base de datos se ejecutarán mediante rutinas `async / await`. Esto garantiza que el *Event Loop* de FastAPI nunca se bloquee, permitiendo alta concurrencia incluso cuando el middleware inyecta latencia artificial al pasante.
* **Paradigma Funcional (Mutación de Datos):** La lógica correspondiente a las trampas (ofuscación, alteración de llaves JSON, empaquetado binario TLE) se programará utilizando **funciones puras**. Al evitar efectos secundarios (*side effects*) y mutaciones de estado global, se garantiza que si el sistema devuelve un dato erróneo al pasante, es estrictamente por diseño (una trampa activa) y no por un bug impredecible en el backend.

## 4. Patrones de Diseño Tácticos
Se establecen los siguientes patrones estructurales para mantener el código *DRY* (Don't Repeat Yourself) y modular:

* **Patrón Middleware (Interceptores):** Es el pilar del sistema de evaluación. Se utilizarán middlewares a nivel de aplicación para interceptar todas las peticiones entrantes y salientes de forma centralizada.
    * *Auth Middleware:* Recalcula y valida el hash criptográfico (Token + Semilla + Timestamp) previniendo ataques de repetición.
    * *Chaos Middleware:* Consulta las reglas activas en la base de datos y aplica mutaciones de red (errores HTTP 5xx, latencia) sin ensuciar el código individual de cada enrutador.
* **Inyección de Dependencias (DI):** Se aprovechará el sistema nativo `Depends()` de FastAPI. Los servicios, la sesión de SQLite y el estado de Redis se inyectarán dinámicamente en los endpoints, facilitando el aislamiento de componentes y el testing unitario.
* **Patrón CRUD Simplificado:** Como punto de equilibrio para evitar la sobreingeniería de un patrón *Repository* abstracto, las consultas a SQLite se encapsularán en funciones CRUD imperativas y directas. El resto del sistema interactuará con estas funciones sin acoplarse al dialecto SQL subyacente.