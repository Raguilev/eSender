import os
import shutil
import json
from datetime import datetime

def create_rpa_package(json_path: str):
    with open(json_path, encoding="utf-8") as f:
        config = json.load(f)

    rpa_name = config["rpa"]["nombre"].replace(" ", "_")
    package_name = rpa_name
    package_dir = os.path.join("RPAs_Generados", package_name)

    # Si ya existe, lo eliminamos para evitar conflictos
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir, exist_ok=True)

    # Guardar JSON de configuración
    json_dest = os.path.join(package_dir, "rpa_email.json")
    with open(json_dest, "w", encoding="utf-8") as f_out:
        json.dump(config, f_out, indent=4, ensure_ascii=False)

    # Crear run_rpa.py (script de ejecución modular)
    run_path = os.path.join(package_dir, "run_rpa.py")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(generate_run_rpa_script())

    # Crear ejecutar.vbs
    vbs_name = f"ejecutar_{rpa_name}.vbs"
    vbs_path = os.path.join(package_dir, vbs_name)
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(generate_vbs_script())

    # Crear crear_tarea.bat
    bat_path = os.path.join(package_dir, "crear_tarea.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(generate_bat_script(rpa_name, vbs_name, config.get("programacion", {})))

    print(f"RPA empaquetado en: {package_dir}")

def generate_run_rpa_script():
    return '''\
import os
import json
from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo

CONFIG_PATH = "rpa_email.json"
try:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error al leer el archivo de configuración: {e}")
    exit(1)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

if not rpa.get("url_ruta") or not rpa["url_ruta"][0].get("url"):
    print("URL de acceso no especificada.")
    exit(1)

if correo.get("usar_remoto", False):
    smtp = correo.get("smtp_remoto", {})
    if not smtp.get("usuario") or not smtp.get("clave_aplicacion"):
        print("Credenciales de servidor remoto incompletas.")
        exit(1)
else:
    smtp = correo.get("smtp_local", {})

screenshot_path = None
try:
    screenshot_path, timestamp = ejecutar_navegacion(rpa)
    print(f"Captura generada: {screenshot_path}")
except Exception as e:
    print(f"Error durante la navegación: {e}")
    exit(1)

try:
    enviar_reporte_por_correo(correo, rpa, screenshot_path, timestamp)
    print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")
'''
def generate_vbs_script():
    return '''\
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = WScript.ScriptFullName
WshShell.CurrentDirectory = Left(WshShell.CurrentDirectory, InStrRev(WshShell.CurrentDirectory, "\\") - 1)
WshShell.Run "cmd /c python run_rpa.py rpa_email.json", 0, False
'''

def generate_bat_script(rpa_name, vbs_filename, programacion):
    frecuencia = programacion.get("frecuencia", "hourly")
    intervalo = programacion.get("intervalo", 6)
    hora_inicio = programacion.get("hora_inicio", "00:00")

    return f'''\
@echo off
SET NOMBRE_TAREA={rpa_name}
SET CARPETA=%~dp0
SET VBS_PATH=%CARPETA%{vbs_filename}

schtasks /create /f /tn "%NOMBRE_TAREA%" ^
    /tr "wscript.exe \\"%VBS_PATH%\\"" ^
    /sc {frecuencia} /mo {intervalo} /st {hora_inicio} ^
    /ru SYSTEM

echo Tarea programada '%NOMBRE_TAREA%' creada exitosamente.
pause
'''
