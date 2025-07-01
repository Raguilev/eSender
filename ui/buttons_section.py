from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QMessageBox
from deploy_handler import create_rpa_package
from ui.config_loader import save_config

def conectar_botones_accion(parent):
    parent.save_button.clicked.connect(lambda: save_config(parent))
    parent.test_button.clicked.connect(lambda: ejecutar_rpa(parent))
    parent.deploy_button.clicked.connect(lambda: hacer_deploy(parent))

def ejecutar_rpa(parent):
    try:
        json_path = save_config(parent)
        if not json_path:
            return  # Ya se mostró el error
        parent.process = QProcess(parent)
        parent.process.setProgram("python")
        parent.process.setArguments(["run_rpa.py"])
        parent.process.readyReadStandardOutput.connect(lambda: mostrar_stdout(parent))
        parent.process.readyReadStandardError.connect(lambda: mostrar_stderr(parent))
        parent.process.finished.connect(lambda code, status: finalizar_proceso(parent, code, status))
        parent.process.start()
    except Exception as e:
        QMessageBox.critical(parent, "Error al iniciar", f"No se pudo ejecutar el RPA:\n{e}")

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