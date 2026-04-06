# 🛰️ Sistema DOMO - Centro de Comando (Master Control)

Este documento contiene los enlaces de acceso y credenciales críticas para la gestión del Sistema DOMO en producción.

---

## 🌐 Enlaces de Producción (Render)
**URL Base:** `https://sistema-domo.onrender.com`

### 🛠️ Paneles Administrativos
*   **Game Master Dashboard (Control de Caos):**
    [https://sistema-domo.onrender.com/static/gm/index.html](https://sistema-domo.onrender.com/static/gm/index.html)
    *Uso: Activar/desactivar las 8 trampas y monitorear métricas.*

*   **Domo Ops Dashboard (Referencia Oficial):**
    [https://sistema-domo.onrender.com/static/domo/index.html](https://sistema-domo.onrender.com/static/domo/index.html)
    *Uso: Tu visor oficial de datos espaciales sin (o con) trampas.*

*   **Documentación de API (Swagger):**
    [https://sistema-domo.onrender.com/docs](https://sistema-domo.onrender.com/docs)

### 📂 Endpoints de la API (Para el Pasante)
*   **Init/Handshake:** `https://sistema-domo.onrender.com/api/v1/init/`
*   **Weather:** `https://sistema-domo.onrender.com/api/v1/intern/weather`
*   **NEOs:** `https://sistema-domo.onrender.com/api/v1/intern/neos`
*   **Satellites:** `https://sistema-domo.onrender.com/api/v1/intern/satellites`
*   **Launches:** `https://sistema-domo.onrender.com/api/v1/intern/launches`
*   **Conjunctions:** `https://sistema-domo.onrender.com/api/v1/intern/conjunctions`
*   **APOD:** `https://sistema-domo.onrender.com/api/v1/intern/apod`

---

## 🔑 Credenciales y Seguridad
*   **Master Crypto Seed:** `DOMO_SECURE_UPLINK_PROTOCOL_2026_X`
*   **NASA API Key:** `AUVRRW9j4x8RC76w9CLqLAvCNV0YgZNLcMFE0YVe`

---

## 🕵️ Herramientas de Auditoría Local
Ejecuta estos comandos desde la terminal en la raíz del proyecto para auditar el servidor de Render:

1.  **Auditar Trampas Activas:**
    `.\venv\Scripts\python.exe domo_spy.py`
    *(Nota: Asegúrate de que ROOT_URL en el script apunte a tu URL de Render).*

2.  **Simular Comportamiento Completo del Pasante:**
    `.\venv\Scripts\python.exe test_all_traps.py`

3.  **Resetear Todas las Trampas (Limpieza):**
    `.\venv\Scripts\python.exe reset_traps.py`

---

## ⚠️ Recordatorio de Producción
*   **Plan Free de Render:** El servidor se "duerme" tras 15 min de inactividad. La primera petición tardará ~40s en despertar.
*   **Persistencia:** Sin "Persistent Disk", los cambios en las trampas y las métricas se reiniciarán si el servidor se apaga.
