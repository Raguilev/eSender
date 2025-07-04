import os
import shutil
import json
import zipfile
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

try:
    BASE_PATH = os.path.dirname(file)
except NameError:
    BASE_PATH = os.getcwd()

def create_rpa_package(json_path: str, modo: str = "zip"):
    with open(json_path, encoding="utf-8") as f:
        config = json.load(f)

    rpa_name = config["rpa"]["nombre"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"{rpa_name}_{timestamp}"

    if modo == "exe":
        base_dir = os.path.join("RPAs_Generados", "Deploy_Exe", package_name)
    else:
        base_dir = os.path.join("RPAs_Generados", "Deploy_Zip", package_name)

    os.makedirs(base_dir, exist_ok=True)

    # === Guardar JSON de configuración ===
    json_dest = os.path.join(base_dir, "rpa_email.json")
    with open(json_dest, "w", encoding="utf-8") as f_out:
        json.dump(config, f_out, indent=4, ensure_ascii=False)

    # === Crear script run_rpa.py ===
    run_path = os.path.join(base_dir, "run_rpa.py")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(generate_run_rpa_script())

    # Copiar carpeta rpa_runner
    origen_runner = os.path.join(BASE_PATH, "rpa_runner")
    destino_runner = os.path.join(base_dir, "rpa_runner")
    shutil.copytree(origen_runner, destino_runner, dirs_exist_ok=True)

    # Crear archivo .bat para programar tarea
    crear_bat_scheduler(base_dir, config["rpa"]["nombre"])

    # Crear instrucciones
    crear_instrucciones(base_dir, modo)

    # Crear empaquetado
    if modo == "exe":
        generar_exe(base_dir)
    else:
        generar_zip(base_dir)

    print(f"RPA desplegado correctamente en: {base_dir}")

def generar_zip(folder_path: str):
    zip_path = folder_path + ".zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, folder_path)
                zipf.write(filepath, arcname)
    print(f"ZIP generado en: {zip_path}")

def generar_exe(folder_path: str):
    script_path = os.path.join(folder_path, "run_rpa.py")
    cmd = [
        "pyinstaller",
        "--onefile",
        "--clean",
        "--distpath", folder_path,
        "--workpath", os.path.join(folder_path, "build"),
        "--specpath", os.path.join(folder_path, "spec"),
        script_path
    ]
    print("Generando ejecutable...")
    subprocess.run(cmd, check=True)
    print("Ejecutable generado en:", folder_path)

def generate_run_rpa_script():
    return '''import os
import sys
import json
from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo

if len(sys.argv) < 2:
    config_path = "rpa_email.json"
else:
    config_path = sys.argv[1]

if not os.path.exists(config_path):
    print(f"No se encontró el archivo de configuración: {config_path}")
    sys.exit(1)

with open(config_path, encoding="utf-8") as f:
    config = json.load(f)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

if not rpa.get("url_ruta") or not rpa["url_ruta"][0].get("url"):
    print("Debes especificar al menos una URL de acceso inicial.")
    sys.exit(1)

if correo.get("usar_remoto"):
    smtp = correo.get("smtp_remoto", {})
    if not smtp.get("usuario") or not smtp.get("clave_aplicacion"):
        print("Faltan credenciales para SMTP remoto.")
        sys.exit(1)
else:
    smtp = correo.get("smtp_local", {})
    if not smtp.get("servidor"):
        print("Advertencia: no se especificó un servidor SMTP local.")

try:
    capturas, timestamp = ejecutar_navegacion(rpa)
    print(f"{len(capturas)} capturas generadas.")
except Exception as e:
    print(f"Error durante la navegación: {e}")
    sys.exit(1)

try:
    enviar_reporte_por_correo(correo, rpa, capturas, timestamp)
    print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")
    sys.exit(1)
'''

def crear_instrucciones(folder_path: str, modo: str):
    instrucciones_path = os.path.join(folder_path, "instrucciones.txt")
    with open(instrucciones_path, "w", encoding="utf-8") as f:
        f.write("INSTRUCCIONES DE USO\n\n")
        if modo == "zip":
            f.write("1. Asegúrate de tener Python 3 instalado.\n")
            f.write("2. Haz doble clic en 'programar_tarea_rpa.bat' para registrar la tarea.\n")
            f.write("3. Luego ejecuta 'run_rpa.py' directamente.\n")
        else:
            f.write("1. Haz doble clic en 'programar_tarea_rpa.bat' para registrar la tarea.\n")
            f.write("2. El ejecutable '.exe' ya contiene todo lo necesario.\n")

def crear_bat_scheduler(folder_path: str, rpa_name: str):
    bat_path = os.path.join(folder_path, "programar_tarea_rpa.bat")
    exe_name = f"{rpa_name.replace(' ', '_')}.exe"
    comando = f'''@echo off
SCHTASKS /CREATE /TN "RPA_{rpa_name}" /TR "%CD%\\{exe_name}" /SC DAILY /ST 09:00 /F
pause
'''
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(comando)

def preguntar_modo_deploy(parent) -> str:
    msg = QMessageBox(parent)
    msg.setWindowTitle("Modo de despliegue")
    msg.setText("¿Cómo deseas empaquetar este RPA?")
    msg.setInformativeText("Selecciona el formato de distribución:")
    zip_btn = msg.addButton("Generar .ZIP", QMessageBox.AcceptRole)
    exe_btn = msg.addButton("Generar .EXE", QMessageBox.AcceptRole)
    cancel_btn = msg.addButton("Cancelar", QMessageBox.RejectRole)
    msg.setDefaultButton(zip_btn)
    msg.exec_()

    if msg.clickedButton() == zip_btn:
        return "zip"
    elif msg.clickedButton() == exe_btn:
        return "exe"
    return None