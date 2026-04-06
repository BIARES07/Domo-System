import httpx
import time
import hashlib
import json
import struct
import base64
from datetime import datetime
import asyncio

BASE_URL = "http://127.0.0.1:8000/api/v1"

class DomoTester:
    def __init__(self):
        self.seed = ""
        self.links = {}
        self.session_id = ""
        self.last_init_time = 0

    def print_header(self, title):
        print(f"\n{'#'*60}")
        print(f"## {title.center(56)} ##")
        print(f"{'#'*60}")

    async def perform_handshake(self, client):
        print(f"[*] Connecting to {BASE_URL}/init/ ...")
        try:
            res = await client.get(f"{BASE_URL}/init/")
            res.raise_for_status()
            data = res.json()
            self.seed = data["crypto_seed"]
            self.links = data["links"]
            self.session_id = data["session_id"]
            self.last_init_time = int(time.time())
            
            print(f"[+] Handshake Successful.")
            print(f"    - Seed: {self.seed}")
            print(f"    - Session: {self.session_id}")
            
            if datetime.now().strftime("%Y-%m-%d") in self.links["weather"]:
                print("[!] DETECTED: Dynamic HATEOAS Trap is active (URLs include dates).")
            else:
                print("[+] URLs seem static/standard.")
        except Exception as e:
            print(f"[-] Handshake Failed: {e}")

    def get_auth_headers(self, force_expired=False):
        timestamp = int(time.time())
        if force_expired:
            timestamp -= 7200 # 2 hours ago
            print("[!] Sending EXPIRED timestamp to test Seed Rotation...")
            
        t_str = str(timestamp)
        payload = self.seed + t_str
        token = hashlib.sha256(payload.encode()).hexdigest()
        return {
            "X-Domo-Time": t_str,
            "X-Domo-Token": token,
            "X-Domo-Session": self.session_id
        }

    def read_field(self, payload, key, fallback=None):
        if not isinstance(payload, dict):
            return fallback
        if key in payload:
            return payload[key]
        mutated_key = f"{key}_cruda"
        if mutated_key in payload:
            return payload[mutated_key]
        return fallback

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

    def analyze_response(self, response, endpoint_name):
        print(f"\n--- Analyzing {endpoint_name} ---")
        
        if response.status_code != 200:
            print(f"[!] DETECTED: HTTP Chaos (Level 2). Status: {response.status_code}")
            print(f"    Body: {response.text}")
            return

        content_type = response.headers.get("Content-Type", "")
        if "application/octet-stream" in content_type:
            print("[!] DETECTED: Binary Payload (Level 3).")
            self.decode_binary_satellites(response.content)
            return

        try:
            data = response.json()
            if isinstance(data, dict) and data.get("status") == "SESSION_ENCRYPTED_UPGRADE_REQUIRED":
                print("[!] DETECTED: Seed Rotation (Advanced). Data is Base64 encoded.")
                raw_payload = base64.b64decode(data["payload_buffer"]).decode()
                print(f"    Decoded Data (first 100 chars): {raw_payload[:100]}...")
                data = json.loads(raw_payload)

            if isinstance(self.read_field(data, "manifest"), list):
                print("[!] DETECTED: Launch Window Fragmentation.")

            if isinstance(self.read_field(data, "alerts"), list):
                print("[!] DETECTED: Conjunction Signal Scramble.")
            
            is_mutated = False
            extracted_items = self.extract_items(data)
            sample_item = extracted_items[0] if extracted_items else data
            if isinstance(sample_item, dict):
                for k in sample_item.keys():
                    if k.endswith("_cruda"):
                        is_mutated = True
                        break
            
            if is_mutated:
                print("[!] DETECTED: JSON Mutation (Level 1). Keys modified with '_cruda'.")
            
            is_drifted = False
            if isinstance(sample_item, dict):
                for v in sample_item.values():
                    if isinstance(v, str) and ("km/s" in v or "deg" in v or "units" in v):
                        is_drifted = True
                        break
            if is_drifted:
                print("[!] DETECTED: Schema Drift (Advanced). Numbers converted to strings with units.")

            if isinstance(self.read_field(data, "items"), list) and self.read_field(data, "range"):
                print("[!] DETECTED: Inconsistent Paging (Advanced).")
                print(f"    Range: {self.read_field(data, 'range')} | Total: {self.read_field(data, 'total_count')}")
                print(f"    Items received: {len(self.read_field(data, 'items', []))}")

            if isinstance(sample_item, dict) and self.read_field(sample_item, "launch_vector"):
                print(f"    Launch Vector: {self.read_field(sample_item, 'launch_vector')}")

            if isinstance(sample_item, dict) and self.read_field(sample_item, "threat_band"):
                print(f"    Threat Band: {self.read_field(sample_item, 'threat_band')}")

            print("[+] Sample Data Received:")
            print(json.dumps(data if not isinstance(data, list) else data[:1], indent=2))

        except Exception as e:
            print(f"[-] Error analyzing JSON response: {e}")

    def decode_binary_satellites(self, content):
        print(f"    Payload size: {len(content)} bytes")
        record_size = 20
        num_records = len(content) // record_size
        print(f"    Attempting to decode {num_records} satellite records...")
        for i in range(min(3, num_records)):
            chunk = content[i*record_size : (i+1)*record_size]
            norad_id, lat, lon, alt, vel = struct.unpack("<Iffff", chunk)
            print(f"    - Record {i+1}: ID={norad_id}, Lat={lat:.2f}, Vel={vel:.2f}")

    async def run_tests(self):
        self.print_header("DOMO SYSTEM COMPREHENSIVE TEST")
        async with httpx.AsyncClient() as client:
            await self.perform_handshake(client)
            
            # Test 1: Weather
            headers = self.get_auth_headers()
            try:
                res = await client.get(f"http://127.0.0.1:8000{self.links['weather']}", headers=headers, timeout=10)
                self.analyze_response(res, "SPACE WEATHER")
            except httpx.TimeoutException:
                print("[!] DETECTED: Network Latency (Level 2). Request timed out.")
            except Exception as e:
                print(f"[-] Request error: {e}")

            # Test 2: Launches
            print("\n--- Testing Launches Feed ---")
            headers = self.get_auth_headers()
            res = await client.get(f"http://127.0.0.1:8000{self.links['launches']}", headers=headers)
            self.analyze_response(res, "LAUNCHES")

            # Test 3: Conjunctions
            print("\n--- Testing Conjunctions Feed ---")
            headers = self.get_auth_headers()
            res = await client.get(f"http://127.0.0.1:8000{self.links['conjunctions']}", headers=headers)
            self.analyze_response(res, "CONJUNCTIONS")

            # Test 4: Satellites
            print("\n--- Testing Satellites with Paging Header ---")
            headers = self.get_auth_headers()
            headers["X-Domo-Range"] = "items=0-9"
            res = await client.get(f"http://127.0.0.1:8000{self.links['satellites']}", headers=headers)
            self.analyze_response(res, "SATELLITES")

            # Test 5: Anti-Replay Barrier
            print("\n--- Testing Anti-Replay Barrier (Expired Header) ---")
            headers = self.get_auth_headers(force_expired=True)
            res = await client.get(f"http://127.0.0.1:8000{self.links['apod']}", headers=headers)
            self.analyze_response(res, "APOD (EXPIRED TIMESTAMP)")

if __name__ == "__main__":
    tester = DomoTester()
    asyncio.run(tester.run_tests())
