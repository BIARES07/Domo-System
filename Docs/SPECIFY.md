# Sistema DOMO: Especificación de Requerimientos (Fase 1 - SDD)

## 1. Visión General del Sistema
El Sistema DOMO es una plataforma de arquitectura dual. Funciona simultáneamente como un Centro de Comando personal, inmersivo y de alto rendimiento para el monitoreo de eventos espaciales en tiempo real, y como un API Gateway gamificado. Su propósito subyacente es servir como un campo de entrenamiento y evaluación para un pasante (TSU o junior), obligándolo a construir un cliente robusto frente a una API intencionalmente hostil, fragmentada y desafiante.

## 2. Actores del Sistema
* **Administrador (Game Master):** Consume los datos espaciales a través de su propia interfaz cliente inmersiva (el DOMO principal). Controla el flujo de datos del API Gateway, monitorea las métricas del pasante en tiempo real y calibra la dificultad técnica mediante un panel de control.
* **Pasante (Candidato):** Desarrollador que debe construir su propio cliente DOMO consumiendo los micro-endpoints del Gateway, manejando asincronía compleja, aplicando ingeniería inversa básica y superando obstáculos técnicos no documentados.

## 3. Interfaz del Centro de Comando (Cliente Administrador DOMO)
El cliente principal es una aplicación optimizada para entornos multi-monitor, permitiendo separar la visualización espacial del tablero de evaluación. 

* **Panel de Clima Espacial (Space Weather):** Una línea de tiempo vertical (*ticker*) de alertas tempranas. Las llamaradas solares se listan con íconos codificados por color según su clasificación (X, M). Al interactuar, despliega el gráfico de impacto estimado extrayendo datos de la API DONKI.
* **Radar Táctico de Objetos Cercanos (NEOs):** Un *display* tipo radar en 2D polar. La Tierra es el centro; los asteroides (API NeoWs) se posicionan según su distancia relativa y vector. Los catalogados como "potencialmente peligrosos" generan una alerta visual y un halo de advertencia.
* **Visor Multimedia (APOD):** Galería interactiva en alta resolución que ocupa un cuadrante primario. Permite navegar por el mes actual y reproducir *iframes*/videos directamente en el panel.
* **Mapa Orbital de Satélites (Monitoreo TLE):** Renderizado en tiempo real que dibuja las trayectorias de los satélites activos (CelesTrak). Al seleccionar un nodo, la cámara hace foco interpolando los datos TLE y muestra una ventana de telemetría con el designador NORAD, altitud y velocidad.

## 4. Arquitectura de Micro-Endpoints (API Gateway Fragmentada para el Pasante)
El Gateway abandona el modelo monolítico para forzar la orquestación de datos y penalizar la fuerza bruta.

* **Nodo de Entrada (`/api/v1/init`):** Único endpoint documentado. Retorna el token base temporal y pistas para descubrir la topología de la API.
* **Módulo: Clima Espacial**
    * `/solar/flares/active`: Arreglo de IDs de llamaradas recientes.
    * `/solar/flares/{id}/metrics`: Clasificación y tiempo de impacto por ID.
* **Módulo: Objetos Cercanos**
    * `/asteroids/today/references`: IDs de asteroides del día.
    * `/asteroids/kinematics/{ref}`: Exclusivamente velocidad y distancia.
    * `/asteroids/hazards/{ref}`: Diámetro y bandera booleana de peligro.
* **Módulo: Imagen Astronómica**
    * `/media/apod/metadata`: Título, descripción y tipo de medio.
    * `/media/apod/blob`: Binario o URL firmada del recurso visual.
* **Módulo: Monitoreo Orbital (Alta Dificultad)**
    * `/telemetry/nodes/active`: Listado de identificadores NORAD.
    * `/telemetry/node/{id}/tle`: Datos orbitales crudos. Diseñado para que el pasante parsee la información y alimente su propio display de radar.
    * `/catalog/{id}/info`: Metadata (nombre, fecha de lanzamiento).

## 5. Autenticación y Sistema de Trampas (Anti-IA / Anti-Facilismo)
El Administrador dispondrá de un panel con interruptores (*toggles*) para activar/desactivar reglas de comportamiento global o por pasante.

* **Autenticación (Desafío-Respuesta):** Sin API Keys estáticas. El pasante debe calcular un *hash* criptográfico (ej. SHA256) combinando un Token, una semilla y un *Timestamp* en tiempo real para cada petición.
* **Modo Pacífico (Bypass):** Desactiva todas las trampas para facilitar el inicio del desarrollo.
* **Mutación de Estructuras (Nivel 1):** Middleware que altera aleatoriamente las claves de los JSON de respuesta (ej. `distance_km` muta a `dist_kilo`).
* **Caos de Red y Rate Limiting (Nivel 2):** Inyección de latencia artificial y errores HTTP (500, 429, 503) aleatorios para obligar la implementación de reintentos (*exponential backoff*).
* **Ofuscación Binaria (Nivel 3):** Empaqueta respuestas críticas (ej. telemetría TLE) en un flujo de bytes puros sin esquema JSON, requiriendo desempaquetado a bajo nivel y comprensión de estructuras de memoria.

## 6. Métricas de Evaluación (El "Gran Hermano")
El DOMO del Administrador mantendrá un flujo de notificaciones y telemetría del pasante:

* **Tasa de Descubrimiento:** Nodos descubiertos exitosamente sobre el total oculto.
* **Resiliencia al Caos:** Caídas de la aplicación del pasante vs. recuperaciones automáticas.
* **Eficiencia de Consumo:** Penalizaciones por saturar el Gateway con peticiones secuenciales, forzando la implementación de caché local y concurrencia.
* **Tiempo de Recuperación:** Tiempo transcurrido entre un fallo provocado por una trampa y la resolución exitosa del problema.