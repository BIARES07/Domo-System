import requests
import time
import hashlib
import json
import struct

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_separator(title):
    print(f"\n{'='*50}\n--- {title} ---\n{'='*50}")

def main():
    print_separator("PASO 1: Inicialización (Handshake)")
    try:
        # El pasante hace un GET a /init/ sin headers
        response = requests.get(f"{BASE_URL}/init/")
        response.raise_for_status()
        init_data = response.json()
        
        crypto_seed = init_data.get("crypto_seed")
        session_id = init_data.get("session_id")
        print(f"[+] Conexión exitosa.")
        print(f"[+] Semilla secreta recibida: {crypto_seed}")
        print(f"[+] Session ID recibida: {session_id}")
        print(f"[+] Instrucciones: {init_data.get('instructions')}")
        
    except Exception as e:
        print(f"[-] Error conectando al servidor: {e}")
        return

    print_separator("PASO 2: Generar Headers Criptográficos")
    # Generamos el timestamp
    current_time = str(int(time.time()))
    
    # Generamos el token (SHA256 de seed + time)
    payload = crypto_seed + current_time
    token = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    
    headers = {
        "X-Domo-Time": current_time,
        "X-Domo-Token": token,
        "X-Domo-Session": session_id
    }
    print(f"[+] Headers generados:")
    print(f"    X-Domo-Time: {current_time}")
    print(f"    X-Domo-Token: {token}")

    print_separator("PASO 3: Consumir API Hostil (Ej: Clima Espacial)")
    try:
        # Hacemos la petición con los headers
        weather_response = requests.get(f"{BASE_URL}/intern/weather", headers=headers)
        
        # Revisamos si caímos en la trampa HTTP (500, 429, 503)
        if weather_response.status_code != 200:
            print(f"[-] ¡TRAMPA HTTP ACTIVADA! Código de error: {weather_response.status_code}")
            print(f"    Cuerpo: {weather_response.text}")
        else:
            print(f"[+] Petición exitosa (200 OK)")
            data = weather_response.json()
            
            # Revisamos si caímos en la trampa de mutación JSON
            # Comprobamos si las llaves normales existen, o si tienen el sufijo '_cruda'
            if len(data) > 0 and 'flrID_cruda' in data[0]:
                print("[!] ¡TRAMPA DE MUTACIÓN JSON ACTIVADA! Las llaves fueron alteradas:")
            else:
                print("[+] JSON normal recibido:")
                
            print(json.dumps(data[:1], indent=2)) # Imprime solo el primer elemento para no saturar

    except requests.exceptions.RequestException as e:
        print(f"[-] Error de conexión (Quizás caíste en la trampa de latencia y dio timeout): {e}")

    print_separator("PASO 4: Consumir Satélites (Trampa Binaria)")
    try:
        # Generamos headers frescos para evitar expirar (max 30 seg)
        current_time = str(int(time.time()))
        token = hashlib.sha256((crypto_seed + current_time).encode('utf-8')).hexdigest()
        headers = {"X-Domo-Time": current_time, "X-Domo-Token": token, "X-Domo-Session": session_id}

        sat_response = requests.get(f"{BASE_URL}/intern/satellites", headers=headers)
        
        if sat_response.status_code == 200:
            content_type = sat_response.headers.get('Content-Type')
            
            if content_type == 'application/octet-stream':
                print("[!] ¡TRAMPA BINARIA ACTIVADA! Se recibió un flujo de bytes en lugar de JSON.")
                print(f"    Tamaño del payload: {len(sat_response.content)} bytes")
                
                # Ejemplo de cómo el pasante tendría que decodificar el binario
                # (4 bytes Uint para NORAD ID, 4 floats de 4 bytes = 20 bytes por satélite)
                print("    Intentando decodificar primer registro...")
                if len(sat_response.content) >= 20:
                    primer_chunk = sat_response.content[:20]
                    # Formato: '<' (little-endian), 'I' (unsigned int), 'f' (float)
                    norad_id, lat, lon, alt, vel = struct.unpack('<Iffff', primer_chunk)
                    print(f"    -> Decodificado - NORAD ID: {norad_id}, Inclinación: {lat:.2f}, Velocidad: {vel:.2f}")
            else:
                print("[+] Formato JSON normal recibido.")
                print(json.dumps(sat_response.json()[:1], indent=2))
        else:
             print(f"[-] Error HTTP: {sat_response.status_code}")

    except Exception as e:
        print(f"[-] Error procesando satélites: {e}")

if __name__ == "__main__":
    main()