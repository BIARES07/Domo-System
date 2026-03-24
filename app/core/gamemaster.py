import struct
import hashlib
from typing import Any, Dict

class Gamemaster:
    @staticmethod
    def pack_satellite_data(lat: float, lon: float, alt: float, vel: float) -> bytes:
        """
        TSK-4.1: Algoritmo de Empaquetado Binario
        Packs satellite float data into a 16-byte binary structure (4 floats, 4 bytes each, little-endian)
        Format: <ffff (Little Endian, 4 floats)
        """
        return struct.pack('<ffff', lat, lon, alt, vel)

    @staticmethod
    def unpack_satellite_data(data: bytes) -> tuple:
        """Helper to unpack for tests"""
        return struct.unpack('<ffff', data)

    @staticmethod
    def mutate_json(data: Any, suffix: str = "_cruda") -> Any:
        """
        TSK-4.2: Algoritmo de Mutación JSON (Nivel 1)
        Recursively mutates a JSON object (dictionary) by adding a suffix to its keys.
        """
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                new_key = f"{k}{suffix}" if isinstance(k, str) else k
                new_dict[new_key] = Gamemaster.mutate_json(v, suffix)
            return new_dict
        elif isinstance(data, list):
            return [Gamemaster.mutate_json(item, suffix) for item in data]
        else:
            return data

gamemaster = Gamemaster()
