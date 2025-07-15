import os
import json
import tempfile
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QMessageBox
from jsonschema import validate, ValidationError

from constants.constants import SCHEMA_FILE
from ui.config_loader import save_config
from deploy_handler.deploy_handler import create_rpa_package


def conectar_botones_accion(parent):
    parent.save_button.clicked.connect(lambda: save_config(parent))
    parent.test_button.clicked.connect(lambda: ejecutar_rpa_desde_ui(parent))
    parent.deploy_button.clicked.connect(lambda: ejecutar_deploy_desde_ui(parent))


def ejecutar_rpa_desde_ui(parent):
    try:
        config_data = parent.obtener_config_desde_ui()

        with open(SCHEMA_FILE, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
            validate(instance=config_data, schema=schema)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp_file:
            json.dump(config_data, tmp_file, indent=4, ensure_ascii=False)
            config_path = tmp_file.name

        parent.process = QProcess(parent)
        parent.process.setProgram("python")
        parent.process.setArguments(["run_rpa.py", config_path])
        parent.process.readyReadStandardOutput.connect(lambda: mostrar_stdout(parent))
        parent.process.readyReadStandardError.connect(lambda: mostrar_stderr(parent))
        parent.process.finished.connect(lambda code, status: finalizar_proceso(parent, code, status))
        parent.process.start()

    except ValidationError as ve:
        path = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo ejecutar el RPA:\n{str(e)}")


def ejecutar_deploy_desde_ui(parent):
    try:
        json_path = save_config(parent)
        if not json_path:
            return

        create_rpa_package(parent, json_path)

    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Error durante el deploy:\n{str(e)}")


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


def finalizar_proceso(parent, exit_code, _exit_status):
    if exit_code == 0:
        QMessageBox.information(parent, "Éxito", "El RPA se ejecutó correctamente.")
    else:
        QMessageBox.warning(parent, "Error", f"El RPA terminó con errores (código: {exit_code})")