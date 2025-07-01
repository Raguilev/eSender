import os
import json
import glob
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from jsonschema import validate, ValidationError
from constants import PLANTILLA_HTML_POR_DEFECTO, RUTA_CONFIG_PRINCIPAL, RUTA_CARPETA_RESPALDOS, SCHEMA_FILE

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
    os.makedirs(RUTA_CARPETA_RESPALDOS, exist_ok=True)
    archivos = glob.glob(os.path.join(RUTA_CARPETA_RESPALDOS, "*.json"))
    if not archivos:
        if os.path.exists(RUTA_CONFIG_PRINCIPAL):
            cargar_desde_archivo(parent, RUTA_CONFIG_PRINCIPAL)
        else:
            QMessageBox.warning(parent, "No encontrado", "No hay configuraciones guardadas.")
        return
    ultimo = max(archivos, key=os.path.getmtime)
    cargar_desde_archivo(parent, ultimo)

def seleccionar_archivo_config(parent):
    os.makedirs(RUTA_CARPETA_RESPALDOS, exist_ok=True)
    archivo, _ = QFileDialog.getOpenFileName(parent, "Seleccionar configuración", RUTA_CARPETA_RESPALDOS, "Archivos JSON (*.json)")
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

        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=data, schema=schema)

        nombre_rpa = data["rpa"].get("nombre", "rpa_email").replace(" ", "_")
        ruta_json = os.path.join(".", f"{nombre_rpa}.json")

        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        os.makedirs(RUTA_CARPETA_RESPALDOS, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        respaldo = os.path.join(RUTA_CARPETA_RESPALDOS, f"{nombre_rpa}_{timestamp}.json")
        shutil.copyfile(ruta_json, respaldo)

        if data["correo"].get("usar_remoto"):
            usuario_remoto = data["correo"].get("smtp_remoto", {}).get("usuario", "")
            remitente = data["correo"].get("remitente", "")
            if remitente and remitente != usuario_remoto:
                QMessageBox.warning(parent, "Advertencia", "El remitente no coincide con el usuario SMTP. Esto puede causar problemas con algunos proveedores.")

        QMessageBox.information(parent, "Éxito", f"Configuración guardada en {ruta_json}")
        return ruta_json

    except ValidationError as ve:
        path = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo guardar: {e}")