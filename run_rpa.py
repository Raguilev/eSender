import os
import sys
import json
from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo

# === Validar argumento de entrada ===
if len(sys.argv) < 2:
    print("Uso: python run_rpa.py <ruta_config.json>")
    sys.exit(1)

config_path = sys.argv[1]

if not os.path.exists(config_path):
    print(f"Archivo no encontrado: {config_path}")
    sys.exit(1)

# === Cargar configuración JSON ===
try:
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"Error al leer el archivo de configuración: {e}")
    sys.exit(1)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

# === Validaciones esenciales ===
# Validar URL inicial
if not rpa.get("url_ruta") or not rpa["url_ruta"][0].get("url"):
    print("Error: Debes especificar al menos una URL de acceso inicial.")
    sys.exit(1)

# Validar credenciales de correo si se usa servidor remoto
usar_remoto = correo.get("usar_remoto", False)
if usar_remoto:
    smtp_remoto = correo.get("smtp_remoto", {})
    if not smtp_remoto.get("usuario") or not smtp_remoto.get("clave_aplicacion"):
        print("Error: Faltan credenciales para el servidor SMTP remoto.")
        sys.exit(1)
else:
    smtp_local = correo.get("smtp_local", {})
    if not smtp_local.get("servidor"):
        print("Advertencia: No se especificó un servidor SMTP local.")

# === Ejecutar navegación y captura ===
try:
    screenshot_path, timestamp = ejecutar_navegacion(rpa)
    print(f"Captura generada: {screenshot_path}")
except Exception as e:
    print(f"Error durante la navegación: {e}")
    sys.exit(1)

# === Enviar correo con captura adjunta ===
try:
    enviar_reporte_por_correo(correo, rpa, screenshot_path, timestamp)
    print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")
    sys.exit(1)