import os
import json
import glob
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from jsonschema import validate, ValidationError
from constants import PLANTILLA_HTML_POR_DEFECTO, SCHEMA_FILE
from constants import CARPETA_CONFIGS



def agregar_botones_carga(parent):
    from PyQt5.QtWidgets import QHBoxLayout, QPushButton
    layout = QHBoxLayout()
    btn_ultima = QPushButton("Cargar última configuración")
    btn_abrir = QPushButton("Abrir configuración...")
    btn_ultima.clicked.connect(lambda: cargar_ultima_config(parent))
    btn_abrir.clicked.connect(lambda: seleccionar_archivo_config(parent))
    layout.addWidget(btn_ultima)
    layout.addWidget(btn_abrir)
    parent.central_layout.addLayout(layout)


def cargar_ultima_config(parent):
    os.makedirs(CARPETA_CONFIGS, exist_ok=True)
    archivos = glob.glob(os.path.join(CARPETA_CONFIGS, "*.json"))
    if not archivos:
        QMessageBox.warning(parent, "No encontrado", "No hay configuraciones guardadas.")
        return
    ultimo = max(archivos, key=os.path.getmtime)
    cargar_desde_archivo(parent, ultimo)


def seleccionar_archivo_config(parent):
    os.makedirs(CARPETA_CONFIGS, exist_ok=True)
    archivo, _ = QFileDialog.getOpenFileName(
        parent, "Seleccionar configuración", CARPETA_CONFIGS, "Archivos JSON (*.json)"
    )
    if archivo:
        cargar_desde_archivo(parent, archivo)


def cargar_desde_archivo(parent, ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)

        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=data, schema=schema)

        parent.set_config(data)
        QMessageBox.information(parent, "Configuración cargada", f"Se cargó la configuración desde:\n{ruta}")
    except ValidationError as ve:
        path = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo cargar la configuración:\n{e}")


def save_config(parent):
    try:
        data = parent.obtener_config_desde_ui()

        # === Validar con JSON Schema ===
        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=data, schema=schema)

        # === Guardar archivo ===
        os.makedirs(CARPETA_CONFIGS, exist_ok=True)
        nombre_rpa = data["rpa"].get("nombre", "rpa_email").replace(" ", "_")
        ruta_json = os.path.join(CARPETA_CONFIGS, f"{nombre_rpa}.json")

        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # === Validación adicional correo ===
        if data["correo"].get("usar_remoto"):
            usuario_remoto = data["correo"].get("smtp_remoto", {}).get("usuario", "")
            remitente = data["correo"].get("remitente", "")
            if remitente and remitente != usuario_remoto:
                QMessageBox.warning(
                    parent,
                    "Advertencia",
                    "El remitente no coincide con el usuario SMTP. Esto puede causar problemas con algunos proveedores."
                )

        QMessageBox.information(parent, "Éxito", f"Configuración guardada en:\n{ruta_json}")
        return ruta_json

    except ValidationError as ve:
        path = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo guardar: {e}")