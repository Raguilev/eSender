import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from typing import Dict


def pad(data: bytes) -> bytes:
    """
    Aplica padding PKCS7 necesario para cifrado AES CBC.
    """
    padding_len = AES.block_size - (len(data) % AES.block_size)
    return data + bytes([padding_len] * padding_len)


def generate_key(output_key_path: str) -> bytes:
    """
    Genera una clave AES-256 (32 bytes) y la guarda en un archivo binario.

    Args:
        output_key_path (str): Ruta del archivo donde guardar la clave

    Returns:
        bytes: Clave generada
    """
    key = get_random_bytes(32)
    with open(output_key_path, "wb") as f:
        f.write(key)
    return key


def encrypt_json(json_data: Dict, key: bytes, output_path: str):
    """
    Cifra un objeto JSON usando AES-CBC y guarda el binario (IV + ciphertext).

    Args:
        json_data (Dict): Diccionario a cifrar
        key (bytes): Clave AES de 32 bytes
        output_path (str): Ruta del archivo .enc de salida
    """
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    plaintext = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
    padded_data = pad(plaintext)
    ciphertext = cipher.encrypt(padded_data)

    with open(output_path, "wb") as f:
        f.write(bytes(iv) + bytes(ciphertext))


def cifrar_configuracion(config: Dict, ruta_enc: str, ruta_key: str):
    """
    Función principal para cifrar configuración:
    Guarda la clave en .key y el archivo cifrado en .enc.

    Args:
        config (Dict): Diccionario de configuración a cifrar
        ruta_enc (str): Ruta del archivo .enc a generar
        ruta_key (str): Ruta del archivo .key a generar
    """
    key = generate_key(ruta_key)
    encrypt_json(config, key, ruta_enc)