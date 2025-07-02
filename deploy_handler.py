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

    os.makedirs("RPAs_Generados", exist_ok=True)

    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir, exist_ok=True)

    # Guardar JSON
    json_dest = os.path.join(package_dir, "rpa_email.json")
    with open(json_dest, "w", encoding="utf-8") as f_out:
        json.dump(config, f_out, indent=4, ensure_ascii=False)

    # Crear scripts
    run_path = os.path.join(package_dir, "run_rpa.py")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(generate_run_rpa_script())

    vbs_name = f"ejecutar_{rpa_name}.vbs"
    vbs_path = os.path.join(package_dir, vbs_name)
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(generate_vbs_script("rpa_email.json"))

    bat_path = os.path.join(package_dir, "crear_tarea.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(generate_bat_script(rpa_name, vbs_name, config.get("programacion", {})))

    print(f"RPA empaquetado correctamente en: {package_dir}")

def generate_run_rpa_script():
    return '''\
import os
import sys
import json
from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo

if len(sys.argv) < 2:
    print("Uso: python run_rpa.py <ruta_config.json>")
    sys.exit(1)

config_path = sys.argv[1]

if not os.path.exists(config_path):
    print(f"Error: archivo no encontrado: {config_path}")
    sys.exit(1)

try:
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"Error al leer el archivo de configuración: {e}")
    sys.exit(1)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

if not rpa.get("url_ruta") or not rpa["url_ruta"][0].get("url"):
    print("Error: debes especificar al menos una URL de acceso inicial.")
    sys.exit(1)

if correo.get("usar_remoto"):
    smtp = correo.get("smtp_remoto", {})
    if not smtp.get("usuario") or not smtp.get("clave_aplicacion"):
        print("Error: faltan credenciales para el servidor SMTP remoto.")
        sys.exit(1)
else:
    smtp = correo.get("smtp_local", {})
    if not smtp.get("servidor"):
        print("Advertencia: no se especificó un servidor SMTP local.")

try:
    capturas, timestamp = ejecutar_navegacion(rpa)
    print(f"{len(capturas)} capturas generadas:")
    for idx, (url, path) in enumerate(capturas):
        print(f"  [{idx + 1}] {url} -> {path}")
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

def generate_vbs_script(json_filename="rpa_email.json"):
    return f'''\
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = WScript.ScriptFullName
WshShell.CurrentDirectory = Left(WshShell.CurrentDirectory, InStrRev(WshShell.CurrentDirectory, "\\") - 1)
WshShell.Run "cmd /c python run_rpa.py {json_filename}", 0, False
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