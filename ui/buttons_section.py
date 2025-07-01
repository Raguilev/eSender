import os
import json
import tempfile
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QMessageBox
from deploy_handler import create_rpa_package
from jsonschema import validate, ValidationError
from constants import SCHEMA_FILE
from ui.config_loader import save_config

def conectar_botones_accion(parent):
    parent.save_button.clicked.connect(lambda: save_config(parent))
    parent.test_button.clicked.connect(lambda: ejecutar_rpa(parent))
    parent.deploy_button.clicked.connect(lambda: hacer_deploy(parent))

def ejecutar_rpa(parent):
    try:
        # === Generar configuración temporal ===
        data = parent.obtener_config_desde_ui()

        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=data, schema=schema)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp:
            json.dump(data, tmp, indent=4, ensure_ascii=False)
            tmp_path = tmp.name

        # === Ejecutar el proceso ===
        parent.process = QProcess(parent)
        parent.process.setProgram("python")
        parent.process.setArguments(["run_rpa.py", tmp_path])
        parent.process.readyReadStandardOutput.connect(lambda: mostrar_stdout(parent))
        parent.process.readyReadStandardError.connect(lambda: mostrar_stderr(parent))
        parent.process.finished.connect(lambda code, status: finalizar_proceso(parent, code, status))
        parent.process.start()

    except ValidationError as ve:
        path = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo ejecutar el RPA:\n{e}")

def hacer_deploy(parent):
    try:
        json_path = save_config(parent)
        if not json_path:
            return
        create_rpa_package(json_path)
        QMessageBox.information(parent, "Deploy", "Se ha generado el paquete del RPA exitosamente.")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Error durante el deploy:\n{e}")

def mostrar_stdout(parent):
    data = parent.process.readAllStandardOutput()
    stdout = bytes(data).decode("utf-8", errors="replace")
    print("STDOUT:\n", stdout)

def mostrar_stderr(parent):
    data = parent.process.readAllStandardError()
    stderr = bytes(data).decode("utf-8", errors="replace")
    print("STDERR:\n", stderr)
    if stderr.strip():
        QMessageBox.critical(parent, "Error en ejecución", stderr)

def finalizar_proceso(parent, exitCode, _exitStatus):
    if exitCode == 0:
        QMessageBox.information(parent, "Éxito", "El RPA se ejecutó correctamente.")
    else:
        QMessageBox.warning(parent, "Error", f"El RPA terminó con errores (código: {exitCode})")