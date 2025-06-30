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

    # Crear main.py actualizado
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
from contextlib import suppress

try:
    with open("rpa_email.json", encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error al leer el archivo JSON: {e}")
    exit(1)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

url_ruta = rpa.get("url_ruta", [])
if not url_ruta or not url_ruta[0].get("url"):
    print("URL de acceso no especificada.")
    exit(1)

usar_remoto = correo.get("usar_remoto", False)
if usar_remoto:
    smtp = correo.get("smtp_remoto", {})
    if not smtp.get("usuario") or not smtp.get("clave_aplicacion"):
        print("Credenciales de servidor remoto incompletas.")
        exit(1)
else:
    smtp = correo.get("smtp_local", {})

os.makedirs("Reportes", exist_ok=True)
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
safe_timestamp = now.strftime("%Y-%m-%d_%H-%M-%S") if correo.get("incluir_fecha") else ""
screenshot_filename = f"captura_{safe_timestamp}.png"
screenshot_path = os.path.join("Reportes", screenshot_filename)

browser = None
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not rpa.get("modo_navegador_visible", False),
            args=["--ignore-certificate-errors"]
        )
        context_args = {
            "viewport": {
                "width": rpa["pantalla"].get("viewport_width", 1920),
                "height": rpa["pantalla"].get("viewport_height", 1080)
            },
            "ignore_https_errors": True
        }
        if rpa["tipo_autenticacion"] == "http_basic":
            creds = rpa.get("http_basic", {})
            if not creds.get("username") or not creds.get("password"):
                raise ValueError("Credenciales http_basic vacías.")
            context_args["http_credentials"] = {
                "username": creds["username"],
                "password": creds["password"]
            }
        context = browser.new_context(**context_args)
        page = context.new_page()
        for idx, ruta in enumerate(url_ruta):
            url_actual = ruta.get("url")
            wait_time = int(ruta.get("wait_time_ms", 0))
            if not url_actual:
                raise ValueError(f"URL vacía en la posición {idx+1}")
            page.goto(url_actual, timeout=60000)
            if idx == 0 and rpa["tipo_autenticacion"] == "form_js":
                form = rpa.get("form_js", {})
                if not form.get("username_value") or not form.get("password_value"):
                    raise ValueError("Credenciales form_js vacías.")
                page.fill(form["username_selector"], form["username_value"])
                page.fill(form["password_selector"], form["password_value"])
                if form["login_action"].lower() == "enter":
                    page.keyboard.press("Enter")
            if wait_time > 0:
                page.wait_for_timeout(wait_time)
        page.screenshot(path=screenshot_path, full_page=rpa["pantalla"].get("captura_pagina_completa", True))
        print(f"Captura guardada en {screenshot_path}")
except Exception as e:
    print(f"Error durante la automatización: {e}")
    screenshot_path = None
finally:
    with suppress(Exception):
        if browser:
            browser.close()

if screenshot_path:
    try:
        plantilla_html = correo.get("cuerpo_html", """
            <p>Estimado equipo,</p>
            <p>Se ha generado correctamente el siguiente reporte automático desde la plataforma <b>{{nombre_rpa}}</b>.</p>
            <p><b>Fecha y hora de captura:</b> {{fecha}}</p>
            <p><b>Vista previa del panel:</b></p>
            <img src="cid:screenshot" alt="Panel" />
            <p><a href="{{url_dashboard}}" target="_blank">Ir al dashboard</a></p>
            <br>
            <p><small>Este mensaje fue generado automáticamente por el sistema de monitoreo. Por favor, no responder.</small></p>
        """)
        url_dashboard = url_ruta[0].get("url", "#")
        cuerpo_html = plantilla_html.replace("{{nombre_rpa}}", rpa.get("nombre", "RPA"))
        cuerpo_html = cuerpo_html.replace("{{fecha}}", timestamp)
        cuerpo_html = cuerpo_html.replace("{{url_dashboard}}", url_dashboard)
        msg = MIMEMultipart()
        subject = correo.get("asunto", "Reporte automático")
        if correo.get("incluir_fecha"):
            subject += f" - {now.strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = correo["remitente"]
        msg["To"] = ", ".join(correo["destinatarios"])
        msg["Cc"] = ", ".join(correo["cc"])
        msg["Subject"] = subject
        msg.attach(MIMEText(cuerpo_html, "html"))
        with open(screenshot_path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
            img.add_header("Content-ID", "<screenshot>")
            img.add_header("Content-Disposition", "inline", filename=screenshot_filename)
            msg.attach(img)
        server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])
        if usar_remoto:
            server.starttls()
            server.login(smtp["usuario"], smtp["clave_aplicacion"])
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