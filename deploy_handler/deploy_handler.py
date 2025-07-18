import os
import json
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

from .encryptor import cifrar_configuracion

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def create_rpa_package(parent, json_path: str) -> None:
    """
    Genera un paquete de despliegue que contiene solo los archivos cifrados: .enc y .key
    """
    # === Leer archivo JSON ===
    try:
        with open(json_path, encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo leer el archivo de configuración:\n{e}")
        return

    # === Validación básica de estructura esperada ===
    try:
        rpa_name = config["rpa"]["nombre"].strip().replace(" ", "_")
    except KeyError:
        QMessageBox.critical(parent, "Error", "Falta el campo obligatorio 'rpa → nombre' en la configuración.")
        return

    # === Crear carpeta base para el paquete ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"{rpa_name}_{timestamp}"
    base_dir = os.path.join("RPAs_Generados", "Deploy_Seguro", package_name)
    os.makedirs(base_dir, exist_ok=True)

    try:
        # === Cifrar configuración ===
        ruta_enc = os.path.join(base_dir, "rpa_config.enc")
        ruta_key = os.path.join(base_dir, "rpa.key")
        cifrar_configuracion(config, ruta_enc, ruta_key)

        # === Confirmación ===
        QMessageBox.information(
            parent,
            "Despliegue exitoso",
            f"El RPA fue generado exitosamente en:\n\n{os.path.abspath(base_dir)}\n\n"
            f"Incluye únicamente los archivos cifrados .enc y .key."
        )
    except Exception as e:
        QMessageBox.critical(parent, "Error durante el despliegue", str(e))