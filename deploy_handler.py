import os
import shutil
import json
import zipfile
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

def create_rpa_package(json_path: str, modo: str = "zip"):
    with open(json_path, encoding="utf-8") as f:
        config = json.load(f)

    rpa_name = config["rpa"]["nombre"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"{rpa_name}_{timestamp}"
    base_dir = os.path.join("RPAs_Generados", package_name)
    os.makedirs(base_dir, exist_ok=True)

    json_dest = os.path.join(base_dir, "rpa_email.json")
    with open(json_dest, "w", encoding="utf-8") as f_out:
        json.dump(config, f_out, indent=4, ensure_ascii=False)

    run_path = os.path.join(base_dir, "run_rpa.py")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(generate_run_rpa_script())

    origen_runner = os.path.join(os.path.dirname(__file__), "rpa_runner")
    destino_runner = os.path.join(base_dir, "rpa_runner")
    shutil.copytree(origen_runner, destino_runner, dirs_exist_ok=True)

    if modo == "exe":
        generar_exe(base_dir)
    else:
        generar_zip(base_dir)

    print(f"RPA desplegado correctamente en: {base_dir}")

def generar_zip(folder_path: str):
    # === 1. Crear archivos auxiliares ===
    bat_path = os.path.join(folder_path, "ejecutar_rpa.bat")
    instrucciones_path = os.path.join(folder_path, "instrucciones.txt")
    programar_bat_path = os.path.join(folder_path, "programar_rpa.bat")

    with open(bat_path, "w", encoding="utf-8") as f:
        f.write('@echo off\n')
        f.write('cd /d %~dp0\n')
        f.write('echo Ejecutando RPA...\n')
        f.write('python run_rpa.py\n')
        f.write('pause\n')

    json_config_path = os.path.join(folder_path, "rpa_email.json")
    with open(json_config_path, encoding="utf-8") as f:
        config = json.load(f)

    nombre_tarea = config["rpa"]["nombre"].replace(" ", "_")
    hora_inicio = config["programacion"].get("hora_inicio", "08:00")
    frecuencia = config["programacion"].get("frecuencia", "daily")
    intervalo = config["programacion"].get("intervalo", 1)

    comando_schtasks = (
        f'schtasks /Create /TN "{nombre_tarea}" '
        f'/TR "%~dp0ejecutar_rpa.bat" '
        f'/SC {frecuencia} /MO {intervalo} /ST {hora_inicio} /RL HIGHEST /F'
    )

    with open(programar_bat_path, "w", encoding="utf-8") as f:
        f.write('@echo off\n')
        f.write('echo Programando tarea en el Programador de Tareas de Windows...\n')
        f.write(comando_schtasks + '\n')
        f.write('echo Tarea programada correctamente.\n')
        f.write('pause\n')

    with open(instrucciones_path, "w", encoding="utf-8") as f:
        f.write("=== INSTRUCCIONES DE USO ===\n\n")
        f.write("1. Ejecuta 'programar_rpa.bat' para registrar la tarea automatizada.\n")
        f.write("2. Puedes revisar o modificar la tarea desde el Programador de Tareas de Windows.\n")
        f.write("3. Para probarlo manualmente, ejecuta 'ejecutar_rpa.bat'.\n")
        f.write("4. Asegúrate de tener Python 3 y Playwright instalado:\n")
        f.write("   python -m pip install playwright\n")
        f.write("   python -m playwright install\n")

    # === 2. Comprimir ===
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
    return '''\
import os
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