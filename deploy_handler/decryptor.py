import json
from Crypto.Cipher import AES
from typing import Dict


def unpad(data: bytes) -> bytes:
    """
    Elimina el padding según el esquema PKCS7 (requerido por AES CBC).
    """
    padding_len = data[-1]
    if padding_len < 1 or padding_len > AES.block_size:
        raise ValueError("Padding inválido o archivo corrupto.")
    return data[:-padding_len]


def descifrar_configuracion(enc_file_path: str, key_file_path: str) -> Dict:
    """
    Descifra un archivo de configuración cifrado con AES-CBC y devuelve el contenido JSON.

    Args:
        enc_file_path (str): Ruta del archivo cifrado (.enc)
        key_file_path (str): Ruta del archivo de clave (.key)

    Returns:
        Dict: Diccionario con la configuración JSON descifrada.
    """
    try:
        # === Leer clave de cifrado ===
        with open(key_file_path, "rb") as f_key:
            key = f_key.read()
            if len(key) != 32:
                raise ValueError("La clave debe tener exactamente 32 bytes (AES-256).")

        # === Leer archivo cifrado ===
        with open(enc_file_path, "rb") as f_enc:
            iv_ciphertext = f_enc.read()
            if len(iv_ciphertext) <= AES.block_size:
                raise ValueError("El archivo cifrado es demasiado pequeño o está incompleto.")

            iv = iv_ciphertext[:AES.block_size]
            ciphertext = iv_ciphertext[AES.block_size:]

        # === Descifrado AES CBC ===
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = cipher.decrypt(ciphertext)
        plaintext = unpad(padded_data)

        # === Conversión a JSON ===
        return json.loads(plaintext.decode("utf-8"))

    except (ValueError, json.JSONDecodeError, FileNotFoundError) as e:
        raise RuntimeError(f"[Descifrado fallido] {e}")