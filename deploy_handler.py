import os
import shutil
import json
from datetime import datetime

def create_rpa_package(json_path: str):
    with open(json_path, encoding="utf-8") as f:
        config = json.load(f)

    rpa_name = config["rpa"]["nombre"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"{rpa_name}_{timestamp}"
    package_dir = os.path.join("RPAs_Generados", package_name)

    os.makedirs(package_dir, exist_ok=True)

    # Guardar JSON de configuración
    json_dest = os.path.join(package_dir, "rpa_email.json")
    with open(json_dest, "w", encoding="utf-8") as f_out:
        json.dump(config, f_out, indent=4, ensure_ascii=False)

    # Crear main.py
    main_path = os.path.join(package_dir, "main.py")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(generate_main_script())

    # Crear ejecutar.vbs
    vbs_name = f"ejecutar_{rpa_name}.vbs"
    vbs_path = os.path.join(package_dir, vbs_name)
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(generate_vbs_script())

    # Crear crear_tarea.bat (usando parámetros de programación)
    bat_path = os.path.join(package_dir, "crear_tarea.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(generate_bat_script(rpa_name, vbs_name, config.get("programacion", {})))

    print(f"RPA empaquetado en: {package_dir}")


def generate_main_script():
    return '''\
import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from playwright.sync_api import sync_playwright

with open("rpa_email.json", encoding="utf-8") as f:
    config = json.load(f)

rpa = config["rpa"]
correo = config["correo"]

os.makedirs("Reportes", exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") if correo["incluir_fecha"] else ""
screenshot_filename = f"captura_{timestamp}.png"
screenshot_path = os.path.join("Reportes", screenshot_filename)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not rpa["modo_navegador_visible"], args=["--ignore-certificate-errors"])
        context_args = {
            "viewport": {
                "width": rpa["pantalla"]["viewport_width"],
                "height": rpa["pantalla"]["viewport_height"]
            },
            "ignore_https_errors": True
        }

        if rpa["tipo_autenticacion"] == "http_basic":
            context_args["http_credentials"] = {
                "username": rpa["http_basic"]["username"],
                "password": rpa["http_basic"]["password"]
            }

        context = browser.new_context(**context_args)
        page = context.new_page()
        page.goto(rpa["url_acceso"], timeout=60000)

        if rpa["tipo_autenticacion"] == "form_js":
            page.fill(rpa["form_js"]["username_selector"], rpa["form_js"]["username_value"])
            page.fill(rpa["form_js"]["password_selector"], rpa["form_js"]["password_value"])
            if rpa["form_js"]["login_action"].lower() == "enter":
                page.keyboard.press("Enter")

        page.wait_for_timeout(rpa["esperas"]["wait_time_after_login"])

        if "url_dashboard" in rpa:
            page.goto(rpa["url_dashboard"])
            page.wait_for_timeout(rpa["esperas"]["wait_time_dashboard"])

        page.screenshot(path=screenshot_path, full_page=rpa["pantalla"]["captura_pagina_completa"])
        browser.close()
        print(f"Captura guardada en {screenshot_path}")

except Exception as e:
    print(f"Error en la automatización: {e}")
    screenshot_path = None

if screenshot_path:
    msg = MIMEMultipart()
    msg["From"] = correo["remitente"]
    msg["To"] = ", ".join(correo["destinatarios"])
    msg["Cc"] = ", ".join(correo["cc"])
    msg["Subject"] = correo["asunto"]

    msg.attach(MIMEText(correo["cuerpo_html"], "html"))

    try:
        with open(screenshot_path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
            img.add_header("Content-ID", "<dv_screenshot>")
            img.add_header("Content-Disposition", "inline", filename=screenshot_filename)
            msg.attach(img)
    except Exception as e:
        print(f"Error adjuntando imagen: {e}")

    try:
        if correo["usar_remoto"]:
            smtp_conf = correo["smtp_remoto"]
            server = smtplib.SMTP(smtp_conf["servidor"], smtp_conf["puerto"])
            server.starttls()
            server.login(smtp_conf["usuario"], smtp_conf["clave_aplicacion"])
        else:
            smtp_conf = correo["smtp_local"]
            server = smtplib.SMTP(smtp_conf["servidor"], smtp_conf["puerto"])

        server.sendmail(
            correo["remitente"],
            correo["destinatarios"] + correo["cc"],
            msg.as_string()
        )
        server.quit()
        print("Correo enviado con éxito.")

    except Exception as e:
        print(f"Error al enviar el correo: {e}")
'''

def generate_vbs_script():
    return '''\
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /k python main.py", 0, False
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
