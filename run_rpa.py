import os
import json
import sys
from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo

# === Parámetro: Ruta del archivo JSON ===
if len(sys.argv) < 2:
    print("Uso: python run_rpa.py <ruta_config.json>")
    sys.exit(1)

CONFIG_PATH = sys.argv[1]

# === Cargar configuración ===
try:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"Error al leer la configuración: {e}")
    sys.exit(1)

rpa = config.get("rpa", {})
correo = config.get("correo", {})

# === Validaciones básicas ===
if not rpa.get("url_ruta") or not rpa["url_ruta"][0].get("url"):
    print("URL de acceso no especificada.")
    sys.exit(1)

if correo.get("usar_remoto", False):
    smtp = correo.get("smtp_remoto", {})
    if not smtp.get("usuario") or not smtp.get("clave_aplicacion"):
        print("Credenciales de servidor remoto incompletas.")
        sys.exit(1)
else:
    smtp = correo.get("smtp_local", {})

# === Ejecutar navegación y captura ===
try:
    screenshot_path, timestamp = ejecutar_navegacion(rpa)
    print(f"Captura generada: {screenshot_path}")
except Exception as e:
    print(f"Error durante la navegación: {e}")
    sys.exit(1)

# === Enviar correo ===
try:
    enviar_reporte_por_correo(correo, rpa, screenshot_path, timestamp)
    print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")