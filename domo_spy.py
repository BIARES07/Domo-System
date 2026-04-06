import httpx
import asyncio
import hashlib
import time
import json
import struct
import base64
from datetime import datetime

# Configuración del Inspector
ROOT_URL = "http://127.0.0.1:8000"
API_V1 = "/api/v1"

class DomoSpy:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.active_traps_db = []
        self.intern_links = {}
        self.session_id = ""

    def log(self, tag, msg, color="0"):
        # Colores: 1=Rojo, 2=Verde, 3=Amarillo, 4=Azul, 5=Magenta, 6=Cian
        print(f"\033[1;3{color}m[{tag}]\033[0m {msg}")

    def read_field(self, payload, key, default=None):
        if not isinstance(payload, dict):
            return default
        if key in payload:
            return payload[key]
        mutated_key = f"{key}_cruda"
        if mutated_key in payload:
            return payload[mutated_key]
        return default

    def extract_items(self, data):
        paged_items = self.read_field(data, "items")
        if isinstance(paged_items, list):
            return paged_items

        manifest = self.read_field(data, "manifest")
        if isinstance(manifest, list):
            return manifest

        alerts = self.read_field(data, "alerts")
        if isinstance(alerts, list):
            return alerts

        if isinstance(data, list):
            return data

        return [data]

    async def sync_admin_status(self):
        """Consulta qué trampas están encendidas en la base de datos"""
        try:
            res = await self.client.get(f"{ROOT_URL}{API_V1}/admin/traps")
            self.active_traps_db = [t["trap_name"] for t in res.json() if t["is_active"]]
            self.log("ADMIN", f"Trampas activas en DB: {', '.join(self.active_traps_db) or 'Ninguna'}", "4")
        except Exception as e:
            self.log("ERR", f"No se pudo conectar con la API de Admin: {e}", "1")

    async def do_handshake(self):
        """Simula el inicio del pasante para obtener rutas y semilla"""
        try:
            res = await self.client.get(f"{ROOT_URL}{API_V1}/init/")
            data = res.json()
            self.intern_links = data["links"]
            self.session_id = data.get("session_id", "")
            self.log("INIT", "Handshake completado. Rutas obtenidas.", "2")
            return data["crypto_seed"]
        except Exception as e:
            self.log("ERR", f"Fallo en handshake: {e}", "1")
            return None

    def get_headers(self, seed, expired=False):
        ts = int(time.time()) if not expired else int(time.time()) - 4000
        token = hashlib.sha256(f"{seed}{ts}".encode()).hexdigest()
        headers = {"X-Domo-Time": str(ts), "X-Domo-Token": token}
        if self.session_id:
            headers["X-Domo-Session"] = self.session_id
        return headers

    async def probe_endpoint(self, name, path, seed):
        """Lanza una sonda a un endpoint y analiza las trampas detectadas"""
        self.log("PROBE", f"Analizando {name}...", "6")
        headers = self.get_headers(seed)
        if name == "SATELLITES":
            headers["X-Domo-Range"] = "items=0-9"
        start = time.time()
        
        try:
            res = await self.client.get(f"{ROOT_URL}{path}", headers=headers, timeout=25.0)
            elapsed = (time.time() - start) * 1000
            
            # --- DETECCIÓN DE TRAMPAS ---
            traps_found = []
            
            # Nivel 2: Latencia (Aumentado a 20s para evitar falsos positivos con APIs externas)
            if elapsed > 20000: 
                traps_found.append(f"LATENCY_TRAP ({elapsed:.0f}ms)")
            
            if res.status_code != 200:
                self.log("TRAP", f"¡CAOS HTTP! Status {res.status_code} en {name}", "1")
                return

            if "application/octet-stream" in res.headers.get("Content-Type", ""):
                traps_found.append("BINARY_TLE")
                self.log("FIND", "Respuesta BINARIA (C-Struct) detectada.", "5")
                return

            data = res.json()
            # Advanced: Seed Rotation
            if isinstance(data, dict) and "payload_buffer" in data:
                traps_found.append("SEED_ROTATION")
                data = json.loads(base64.b64decode(data["payload_buffer"]).decode())

            # Advanced: Inconsistent Paging
            if isinstance(self.read_field(data, "items"), list):
                traps_found.append("INCONSISTENT_PAGING")

            if isinstance(self.read_field(data, "manifest"), list):
                traps_found.append("LAUNCH_WINDOW_FRAGMENTATION")

            if isinstance(self.read_field(data, "alerts"), list):
                traps_found.append("CONJUNCTION_SIGNAL_SCRAMBLE")

            items = self.extract_items(data)
            if items and len(items) > 0:
                sample = items[0]
                if isinstance(sample, dict) and any(str(k).endswith("_cruda") for k in sample.keys()):
                    traps_found.append("JSON_MUTATION")
                if isinstance(sample, dict) and any("units" in str(v) or "km/s" in str(v) for v in sample.values()):
                    traps_found.append("SCHEMA_DRIFT")

                if isinstance(sample, dict) and self.read_field(sample, "launch_vector"):
                    self.log("INFO", f"Launch vector detectado: {self.read_field(sample, 'launch_vector')}", "4")

                if isinstance(sample, dict) and self.read_field(sample, "threat_band"):
                    self.log("INFO", f"Threat band detectado: {self.read_field(sample, 'threat_band')}", "4")

            if traps_found:
                self.log("FIND", f"Trampas detectadas: {', '.join(traps_found)}", "3")
            else:
                self.log("OK", f"Endpoint {name} limpio ({elapsed:.0f}ms).", "2")

        except httpx.TimeoutException:
            self.log("TIME", f"Timeout en {name}. ¡Posible trampa de latencia agresiva!", "1")
        except Exception as e:
            self.log("ERR", f"Error crítico en sonda {name}: {type(e).__name__} - {e}", "1")

    async def run_audit(self):
        print("\n" + "="*50)
        print(" DOMO-SPY v2.2 - COBERTURA TOTAL DE AUDITORÍA")
        print("="*50)

        await self.sync_admin_status()
        seed = await self.do_handshake()

        if not seed: return

        # Probar todos los endpoints operativos del pasante
        await self.probe_endpoint("WEATHER", self.intern_links["weather"], seed)
        await self.probe_endpoint("NEOS", self.intern_links["neos"], seed)
        await self.probe_endpoint("SATELLITES", self.intern_links["satellites"], seed)
        await self.probe_endpoint("LAUNCHES", self.intern_links["launches"], seed)
        await self.probe_endpoint("CONJUNCTIONS", self.intern_links["conjunctions"], seed)
        await self.probe_endpoint("APOD", self.intern_links["apod"], seed)

        # Probar barrera anti-replay con timestamp vencido
        print("-" * 50)
        self.log("TEST", "Verificando barrera anti-replay con Token Expirado...", "5")
        headers = self.get_headers(seed, expired=True)
        try:
            res = await self.client.get(f"{ROOT_URL}{self.intern_links['apod']}", headers=headers)
            if res.status_code == 401:
                self.log("SAFE", "ANTI-REPLAY ACTIVO: Timestamp expirado bloqueado correctamente (401).", "2")
            else:
                self.log("WARN", f"Comportamiento inesperado en anti-replay (Status: {res.status_code})", "1")
        except Exception as e:
            self.log("ERR", f"Fallo en prueba anti-replay: {e}", "1")

if __name__ == "__main__":
    spy = DomoSpy()
    asyncio.run(spy.run_audit())
