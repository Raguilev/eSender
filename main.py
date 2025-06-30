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

# === Preparar ruta de captura ===
os.makedirs("Reportes", exist_ok=True)
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
safe_timestamp = now.strftime("%Y-%m-%d_%H-%M-%S") if correo.get("incluir_fecha") else ""
screenshot_filename = f"captura_{safe_timestamp}.png"
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
                "width": rpa.get("pantalla", {}).get("viewport_width", 1920),
                "height": rpa.get("pantalla", {}).get("viewport_height", 1080)
            },
            "ignore_https_errors": True
        }

        # Autenticación básica si corresponde
        if rpa.get("tipo_autenticacion") == "http_basic":
            creds = rpa.get("http_basic", {})
            if not creds.get("username") or not creds.get("password"):
                raise ValueError("Credenciales http_basic vacías.")
            context_args["http_credentials"] = {
                "username": creds["username"],
                "password": creds["password"]
            }

        context = browser.new_context(**context_args)
        page = context.new_page()

        # Visitar URLs en secuencia
        for idx, ruta in enumerate(url_ruta):
            url_actual = ruta.get("url")
            wait_time = int(ruta.get("wait_time_ms", 0))
            if not url_actual:
                raise ValueError(f"URL vacía en la posición {idx+1}")

            page.goto(url_actual, timeout=60000)

            # Solo hacer login al inicio (si es form_js y es la primera)
            if idx == 0 and rpa.get("tipo_autenticacion") == "form_js":
                form = rpa.get("form_js", {})
                if not form.get("username_value") or not form.get("password_value"):
                    raise ValueError("Credenciales form_js vacías.")
                page.fill(form.get("username_selector", "#username"), form["username_value"])
                page.fill(form.get("password_selector", "#password"), form["password_value"])
                if form.get("login_action", "").lower() == "enter":
                    page.keyboard.press("Enter")

            # Espera entre cargas de cada URL
            if wait_time > 0:
                page.wait_for_timeout(wait_time)

        # Captura de pantalla al final de la secuencia
        page.screenshot(path=screenshot_path, full_page=rpa.get("pantalla", {}).get("captura_pagina_completa", True))
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
        # Cuerpo HTML con reemplazo de variables
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
        msg["From"] = correo.get("remitente", "")
        msg["To"] = ", ".join(correo.get("destinatarios", []))
        msg["Cc"] = ", ".join(correo.get("cc", []))
        msg["Subject"] = subject.strip()
        msg.attach(MIMEText(cuerpo_html, "html"))

        # Adjuntar la imagen
        with open(screenshot_path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
            img.add_header("Content-ID", "<screenshot>")
            img.add_header("Content-Disposition", "inline", filename=screenshot_filename)
            msg.attach(img)

        # Enviar por SMTP
        server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])
        server.ehlo()
        if usar_remoto:
            server.starttls()
            server.ehlo()
            server.login(smtp["usuario"], smtp["clave_aplicacion"])

        destinatarios_full = correo.get("destinatarios", []) + correo.get("cc", [])
        server.sendmail(
            correo.get("remitente", ""),
            destinatarios_full,
            msg.as_string()
        )
        server.quit()
        print("Correo enviado con éxito.")

    except Exception as e:
        print(f"Error al enviar el correo: {e}")
else:
    print("No se generó captura, no se envía correo.")