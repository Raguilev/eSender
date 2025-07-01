import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

def enviar_reporte_por_correo(correo_config, rpa_config, screenshot_path, timestamp):
    usar_remoto = correo_config.get("usar_remoto", False)
    smtp = correo_config.get("smtp_remoto" if usar_remoto else "smtp_local", {})

    if usar_remoto and (not smtp.get("usuario") or not smtp.get("clave_aplicacion")):
        raise ValueError("Credenciales de servidor remoto incompletas.")

    url_dashboard = rpa_config.get("url_ruta", [{}])[-1].get("url", "#")
    now = datetime.now()
    asunto = correo_config.get("asunto", "Reporte automático")
    if correo_config.get("incluir_fecha"):
        asunto += f" - {now.strftime('%Y-%m-%d %H:%M')}"

    # Reemplazo de marcadores en plantilla HTML
    html_base = correo_config.get("cuerpo_html", "")
    cuerpo_html = html_base.replace("{{nombre_rpa}}", rpa_config.get("nombre", "RPA"))
    cuerpo_html = cuerpo_html.replace("{{fecha}}", timestamp)
    cuerpo_html = cuerpo_html.replace("{{url_dashboard}}", url_dashboard)

    lista_urls_html = "".join(f"<li>{ruta.get('url', '')}</li>" for ruta in rpa_config.get("url_ruta", []))
    cuerpo_html = cuerpo_html.replace("{{lista_urls}}", f"<ul>{lista_urls_html}</ul>")

    # === Estructura del mensaje ===
    msg_root = MIMEMultipart('related')
    msg_root['From'] = correo_config.get("remitente", "")
    msg_root['To'] = ", ".join(correo_config.get("destinatarios", []))
    msg_root['Cc'] = ", ".join(correo_config.get("cc", []))
    msg_root['Subject'] = asunto.strip()

    msg_alternative = MIMEMultipart('alternative')
    msg_root.attach(msg_alternative)

    html_part = MIMEText(cuerpo_html, "html", "utf-8")
    msg_alternative.attach(html_part)

    # === Imagen embebida ===
    if os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
            img.add_header("Content-ID", "<screenshot>")
            img.add_header("Content-Disposition", "inline", filename=os.path.basename(screenshot_path))
            msg_root.attach(img)

    # === Enviar correo ===
    server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])
    server.ehlo()
    if usar_remoto:
        server.starttls()
        server.ehlo()
        server.login(smtp["usuario"], smtp["clave_aplicacion"])

    destinatarios_full = correo_config.get("destinatarios", []) + correo_config.get("cc", [])
    server.sendmail(msg_root["From"], destinatarios_full, msg_root.as_string())
    server.quit()
    return True