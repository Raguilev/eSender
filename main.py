import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from playwright.sync_api import sync_playwright
from contextlib import suppress

# === Cargar JSON de configuración ===
try:
    with open("rpa_email.json", encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error al leer el archivo JSON: {e}")
    exit(1)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

# === Validaciones básicas ===
if not rpa.get("url_acceso"):
    print("URL de acceso no especificada.")
    exit(1)

if correo.get("usar_remoto") and (not correo["smtp_remoto"]["usuario"] or not correo["smtp_remoto"]["clave_aplicacion"]):
    print("Credenciales de remoto incompletas.")
    exit(1)

# === Preparar ruta de captura ===
os.makedirs("Reportes", exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") if correo.get("incluir_fecha") else ""
screenshot_filename = f"captura_{timestamp}.png"
screenshot_path = os.path.join("Reportes", screenshot_filename)

# === Automatización con Playwright ===
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
        page.goto(rpa["url_acceso"], timeout=60000)

        if rpa["tipo_autenticacion"] == "form_js":
            form = rpa.get("form_js", {})
            if not form.get("username_value") or not form.get("password_value"):
                raise ValueError("Credenciales form_js vacías.")
            page.fill(form["username_selector"], form["username_value"])
            page.fill(form["password_selector"], form["password_value"])
            if form["login_action"].lower() == "enter":
                page.keyboard.press("Enter")

        page.wait_for_timeout(rpa["esperas"].get("wait_time_after_login", 10000))

        if rpa.get("url_dashboard"):
            page.goto(rpa["url_dashboard"])
            page.wait_for_timeout(rpa["esperas"].get("wait_time_dashboard", 5000))

        page.screenshot(path=screenshot_path, full_page=rpa["pantalla"].get("captura_pagina_completa", True))
        print(f"Captura guardada en {screenshot_path}")

except Exception as e:
    print(f"Error durante la automatización: {e}")
    screenshot_path = None

finally:
    with suppress(Exception):
        if browser:
            browser.close()

# === Enviar correo ===
if screenshot_path:
    try:
        msg = MIMEMultipart()
        subject = correo.get("asunto", "Reporte automático")
        if correo.get("incluir_fecha"):
            subject += f" - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        msg["From"] = correo["remitente"]
        msg["To"] = ", ".join(correo["destinatarios"])
        msg["Cc"] = ", ".join(correo["cc"])
        msg["Subject"] = subject

        msg.attach(MIMEText(correo.get("cuerpo_html", ""), "html"))

        with open(screenshot_path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
            img.add_header("Content-ID", "<screenshot>")
            img.add_header("Content-Disposition", "inline", filename=screenshot_filename)
            msg.attach(img)

        # Conexión SMTP
        if correo["usar_remoto"]:
            smtp = correo["smtp_remoto"]
            server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])
            server.starttls()
            server.login(smtp["usuario"], smtp["clave_aplicacion"])
        else:
            smtp = correo["smtp_local"]
            server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])

        server.sendmail(
            correo["remitente"],
            correo["destinatarios"] + correo["cc"],
            msg.as_string()
        )
        server.quit()
        print("Correo enviado con éxito.")

    except Exception as e:
        print(f"Error al enviar el correo: {e}")
