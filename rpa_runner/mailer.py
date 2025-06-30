import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def enviar_reporte_por_correo(correo_config, rpa_config, screenshot_path, timestamp):
    usar_remoto = correo_config.get("usar_remoto", False)
    smtp = correo_config.get("smtp_remoto" if usar_remoto else "smtp_local", {})

    if usar_remoto and (not smtp.get("usuario") or not smtp.get("clave_aplicacion")):
        raise ValueError("Credenciales de servidor remoto incompletas.")

    # Elegir la última URL visitada como "dashboard"
    url_dashboard = rpa_config.get("url_ruta", [{}])[-1].get("url", "#")
    now = datetime.now()
    asunto = correo_config.get("asunto", "Reporte automático")
    if correo_config.get("incluir_fecha"):
        asunto += f" - {now.strftime('%Y-%m-%d %H:%M')}"

    # Reemplazo de marcadores en el HTML
    html_base = correo_config.get("cuerpo_html", "")
    cuerpo_html = html_base.replace("{{nombre_rpa}}", rpa_config.get("nombre", "RPA"))
    cuerpo_html = cuerpo_html.replace("{{fecha}}", timestamp)
    cuerpo_html = cuerpo_html.replace("{{url_dashboard}}", url_dashboard)

    # Generar lista de URLs visitadas en <ul>
    lista_urls_html = "".join(f"<li>{ruta.get('url', '')}</li>" for ruta in rpa_config.get("url_ruta", []))
    cuerpo_html = cuerpo_html.replace("{{lista_urls}}", f"<ul>{lista_urls_html}</ul>")

    msg = MIMEMultipart()
    msg["From"] = correo_config.get("remitente", "")
    msg["To"] = ", ".join(correo_config.get("destinatarios", []))
    msg["Cc"] = ", ".join(correo_config.get("cc", []))
    msg["Subject"] = asunto.strip()
    msg.attach(MIMEText(cuerpo_html, "html"))

    # Adjuntar imagen del screenshot
    with open(screenshot_path, "rb") as f:
        img = MIMEImage(f.read(), _subtype="png")
        img.add_header("Content-ID", "<screenshot>")
        img.add_header("Content-Disposition", "inline", filename=screenshot_path)
        msg.attach(img)

    server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])
    server.ehlo()
    if usar_remoto:
        server.starttls()
        server.ehlo()
        server.login(smtp["usuario"], smtp["clave_aplicacion"])

    destinatarios_full = correo_config.get("destinatarios", []) + correo_config.get("cc", [])
    server.sendmail(msg["From"], destinatarios_full, msg.as_string())
    server.quit()
    return True