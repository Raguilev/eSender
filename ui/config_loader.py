import os
import json
import glob
import hashlib
from datetime import datetime
from typing import Dict, Optional

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QHBoxLayout, QPushButton
from jsonschema import validate, ValidationError

from constants.constants import PLANTILLA_HTML_POR_DEFECTO, SCHEMA_FILE, CARPETA_CONFIGS


def calcular_hash_config(data: Dict) -> str:
    """
    Calcula un hash SHA-256 del diccionario de configuración JSON.
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def agregar_botones_carga(parent):
    layout = QHBoxLayout()

    btn_nuevo = QPushButton("Nuevo RPA")
    btn_ultima = QPushButton("Cargar última configuración")
    btn_abrir = QPushButton("Abrir configuración...")

    btn_nuevo.clicked.connect(lambda: crear_nueva_config(parent))
    btn_ultima.clicked.connect(lambda: cargar_ultima_config(parent))
    btn_abrir.clicked.connect(lambda: seleccionar_archivo_config(parent))

    layout.addWidget(btn_nuevo)
    layout.addWidget(btn_ultima)
    layout.addWidget(btn_abrir)

    parent.central_layout.addLayout(layout)


def crear_nueva_config(parent):
    """
    Limpia los campos de la UI para iniciar una nueva configuración.
    """
    parent.set_config({})
    parent.last_config_hash = None
    parent.last_saved_path = None
    parent.save_button.setVisible(False)


def cargar_ultima_config(parent):
    os.makedirs(CARPETA_CONFIGS, exist_ok=True)
    archivos = glob.glob(os.path.join(CARPETA_CONFIGS, "*.json"))
    if not archivos:
        QMessageBox.warning(parent, "No encontrado", "No hay configuraciones guardadas.")
        return

    archivo_reciente = max(archivos, key=os.path.getmtime)
    cargar_desde_archivo(parent, archivo_reciente)


def seleccionar_archivo_config(parent):
    os.makedirs(CARPETA_CONFIGS, exist_ok=True)
    archivo, _ = QFileDialog.getOpenFileName(
        parent, "Seleccionar configuración", CARPETA_CONFIGS, "Archivos JSON (*.json)"
    )
    if archivo:
        cargar_desde_archivo(parent, archivo)


def cargar_desde_archivo(parent, ruta: str):
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)

        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=data, schema=schema)

        parent.set_config(data)
        parent.last_config_hash = calcular_hash_config(data)
        parent.last_saved_path = ruta
        parent.save_button.setVisible(False)

        QMessageBox.information(parent, "Configuración cargada", f"Se cargó la configuración desde:\n{ruta}")

    except ValidationError as ve:
        ruta_falla = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo inválido: {ruta_falla}\n\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo cargar el archivo:\n{e}")


def save_config(parent) -> Optional[str]:
    try:
        data = parent.obtener_config_desde_ui()

        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=data, schema=schema)

        os.makedirs(CARPETA_CONFIGS, exist_ok=True)
        nombre_base = data["rpa"].get("nombre", "rpa_email").replace(" ", "_")
        ruta_json = os.path.join(CARPETA_CONFIGS, f"{nombre_base}.json")
        nuevo_hash = calcular_hash_config(data)

        # Validar si ya existe y si cambió
        if os.path.exists(ruta_json):
            if getattr(parent, "last_config_hash", None) != nuevo_hash:
                respuesta = QMessageBox.question(
                    parent,
                    "Archivo ya existe",
                    f"El archivo '{ruta_json}' ya existe.\n¿Deseas sobrescribirlo?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.No
                )
                if respuesta == QMessageBox.Cancel:
                    return
                elif respuesta == QMessageBox.No:
                    nuevo_nombre, _ = QFileDialog.getSaveFileName(
                        parent,
                        "Guardar configuración como...",
                        os.path.join(CARPETA_CONFIGS, f"{nombre_base}_nuevo.json"),
                        "Archivos JSON (*.json)"
                    )
                    if not nuevo_nombre:
                        return
                    if not nuevo_nombre.endswith(".json"):
                        nuevo_nombre += ".json"
                    ruta_json = nuevo_nombre

        # Guardar archivo
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Validación extra para correos remotos
        if data["correo"].get("usar_remoto"):
            smtp_user = data["correo"].get("smtp_remoto", {}).get("usuario", "")
            remitente = data["correo"].get("remitente", "")
            if remitente and remitente != smtp_user:
                QMessageBox.warning(
                    parent,
                    "Advertencia",
                    "El remitente no coincide con el usuario SMTP. Esto puede causar problemas con algunos proveedores."
                )

        parent.last_config_hash = nuevo_hash
        parent.last_saved_path = ruta_json
        parent.save_button.setVisible(False)

        QMessageBox.information(parent, "Éxito", f"Configuración guardada en:\n{ruta_json}")
        return ruta_json

    except ValidationError as ve:
        ruta_falla = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo inválido: {ruta_falla}\n\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo guardar el archivo:\n{e}")
        return None