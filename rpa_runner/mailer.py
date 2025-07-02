import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def enviar_reporte_por_correo(correo_config, rpa_config, capturas, timestamp):
    usar_remoto = correo_config.get("usar_remoto", False)
    smtp = correo_config.get("smtp_remoto" if usar_remoto else "smtp_local", {})

    if usar_remoto and (not smtp.get("usuario") or not smtp.get("clave_aplicacion")):
        raise ValueError("Credenciales de servidor remoto incompletas.")

    now = datetime.now()
    asunto = correo_config.get("asunto", "Reporte automático")
    if correo_config.get("incluir_fecha"):
        asunto += f" - {now.strftime('%Y-%m-%d %H:%M')}"

    # === Plantilla base y marcadores ===
    html_base = correo_config.get("cuerpo_html", "")
    cuerpo_html = html_base.replace("{{nombre_rpa}}", rpa_config.get("nombre", "RPA"))
    cuerpo_html = cuerpo_html.replace("{{fecha}}", timestamp)

    url_dashboard = capturas[-1][0] if capturas else "#"
    cuerpo_html = cuerpo_html.replace("{{url_dashboard}}", url_dashboard)

    lista_urls_html = "".join(
        f"<li>{ruta.get('url', '')}</li>" for ruta in rpa_config.get("url_ruta", [])
    )
    cuerpo_html = cuerpo_html.replace("{{lista_urls}}", f"<ul>{lista_urls_html}</ul>")

    # === Bloque con múltiples capturas ===
    bloque_capturas_html = ""
    for idx, (url, img_path) in enumerate(capturas):
        cid = f"screenshot{idx}"
        bloque_capturas_html += f'''
        <hr>
        <p><b>Captura {idx + 1}:</b> <a href="{url}" target="_blank">{url}</a></p>
        <img src="cid:{cid}" alt="Captura {idx + 1}" style="max-width:100%; border:1px solid #ccc;" />
        '''

    cuerpo_html = cuerpo_html.replace("{{bloque_capturas}}", bloque_capturas_html)

    # === Construcción del mensaje ===
    msg_root = MIMEMultipart('related')
    msg_root['From'] = correo_config.get("remitente", "")
    msg_root['To'] = ", ".join(correo_config.get("destinatarios", []))
    msg_root['Cc'] = ", ".join(correo_config.get("cc", []))
    msg_root['Subject'] = asunto.strip()

    msg_alternative = MIMEMultipart('alternative')
    msg_root.attach(msg_alternative)
    msg_alternative.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    # === Adjuntar imágenes ===
    for idx, (_, img_path) in enumerate(capturas):
        cid = f"screenshot{idx}"
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img = MIMEImage(f.read(), _subtype="png")
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=os.path.basename(img_path))
                msg_root.attach(img)

    # === Validación de destinatarios ===
    destinatarios = correo_config.get("destinatarios", [])
    cc = correo_config.get("cc", [])
    if not destinatarios and not cc:
        raise ValueError("No se ha especificado ningún destinatario ni CC para el correo.")

    # === Enviar correo ===
    server = smtplib.SMTP(smtp["servidor"], smtp["puerto"])
    server.ehlo()
    if usar_remoto:
        server.starttls()
        server.ehlo()
        server.login(smtp["usuario"], smtp["clave_aplicacion"])

    server.sendmail(
        msg_root["From"],
        destinatarios + cc,
        msg_root.as_string()
    )
    server.quit()

    return True