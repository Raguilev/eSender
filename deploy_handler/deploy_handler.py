import os
import shutil
import json
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

from .encryptor import cifrar_configuracion

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def create_rpa_package(parent, json_path: str) -> None:
    """
    Genera un paquete de despliegue cifrado con instrucciones, script de ejecución y programación automática.
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

        # === Copiar ejecutable y motor ===
        _copiar_motor_y_ejecutable(base_dir)

        # === Leer campos de programación desde UI ===
        hora = parent.hora_inicio.text()
        frecuencia = parent.frecuencia.currentText()
        intervalo = parent.intervalo.text()
        sistema = parent.sistema_destino.currentText()

        # === Scripts adicionales ===
        _crear_script_programacion_tarea(base_dir, rpa_name, hora, frecuencia, intervalo, sistema)
        _crear_instrucciones(base_dir, sistema)

        # === Confirmación ===
        QMessageBox.information(
            parent,
            "Despliegue exitoso",
            f"El RPA fue generado exitosamente en:\n\n{os.path.abspath(base_dir)}\n\n"
            f"Incluye archivos cifrados, script de ejecución y tarea programada para {sistema.title()}."
        )
    except Exception as e:
        QMessageBox.critical(parent, "Error durante el despliegue", str(e))


def _copiar_motor_y_ejecutable(destino: str) -> None:
    """
    Copia:
    - `run_rpa_enc.py` renombrado a `run_rpa.py`
    - directorio `rpa_runner/` completo
    - archivo `decryptor.py`
    """
    # === Copiar run_rpa_enc.py renombrado ===
    origen_run = os.path.join(BASE_PATH, "run_rpa_enc.py")
    destino_run = os.path.join(destino, "run_rpa.py")
    shutil.copy2(origen_run, destino_run)

    # === Copiar rpa_runner/ que está fuera de deploy_handler ===
    proyecto_base = os.path.abspath(os.path.join(BASE_PATH, ".."))
    origen_runner = os.path.join(proyecto_base, "rpa_runner")
    destino_runner = os.path.join(destino, "rpa_runner")
    shutil.copytree(origen_runner, destino_runner, dirs_exist_ok=True)

    # === Copiar decryptor.py que está dentro de deploy_handler ===
    origen_decryptor = os.path.join(BASE_PATH, "decryptor.py")
    destino_decryptor = os.path.join(destino, "decryptor.py")
    shutil.copy2(origen_decryptor, destino_decryptor)


def _crear_instrucciones(folder_path: str, sistema: str) -> None:
    """
    Crea un archivo de texto con instrucciones básicas para ejecutar el RPA.
    """
    instrucciones_path = os.path.join(folder_path, "instrucciones.txt")
    with open(instrucciones_path, "w", encoding="utf-8") as f:
        f.write("INSTRUCCIONES DE USO DEL RPA\n\n")
        f.write("1. Asegúrate de tener Python 3 instalado.\n")
        f.write("2. Ejecuta desde consola:\n")
        f.write("   python run_rpa.py rpa_config.enc rpa.key\n")
        f.write("3. También puedes usar el archivo de programación incluido para automatizarlo.\n")


def _crear_script_programacion_tarea(folder_path: str, rpa_name: str, hora: str, frecuencia: str, intervalo: str, sistema: str) -> None:
    """
    Crea un script .bat o .sh para programar automáticamente la ejecución del RPA.
    """
    script_name = "programar_tarea_rpa.bat" if sistema.lower() == "windows" else "programar_tarea_rpa.sh"
    script_path = os.path.join(folder_path, script_name)

    if sistema.lower() == "windows":
        comando = f"""@echo off
SCHTASKS /CREATE /TN "RPA_{rpa_name}" /TR "python %CD%\\run_rpa.py %CD%\\rpa_config.enc %CD%\\rpa.key" /SC {frecuencia.upper()} /MO {intervalo} /ST {hora} /F
pause
"""
    else:
        try:
            hora_24, minuto = hora.split(':')
        except ValueError:
            raise ValueError("El formato de hora debe ser HH:MM (por ejemplo, 14:30).")

        comando = f"""#!/bin/bash
(crontab -l 2>/dev/null; echo "{minuto} {hora_24} */{intervalo} * * cd \\"$(dirname \\"$0\\")\\" && python3 run_rpa.py rpa_config.enc rpa.key") | crontab -
echo "Tarea programada creada para {sistema.title()}."
"""

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(comando)

    if sistema.lower() != "windows":
        os.chmod(script_path, 0o755)