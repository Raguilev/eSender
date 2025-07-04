import os
import sys
import json
from datetime import datetime

# === Asegurar que 'rpa_runner' esté disponible (incluso desde .exe) ===
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, "rpa_runner"))

from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo

# === Validar argumento de entrada: ruta al archivo de configuración ===
if len(sys.argv) < 2:
    print("Uso: run_rpa.exe <ruta_config.json>")
    sys.exit(1)

config_path = sys.argv[1]

if not os.path.isfile(config_path):
    print(f"Error: archivo de configuración no encontrado: {config_path}")
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

# === Ejecutar navegación y generar capturas ===
try:
    capturas, timestamp = ejecutar_navegacion(rpa)
    print(f"{len(capturas)} capturas generadas:")
    for idx, (url, path) in enumerate(capturas):
        print(f"  [{idx + 1}] {url} -> {path}")
except Exception as e:
    print(f"Error durante la navegación: {e}")
    sys.exit(1)

# === Enviar el reporte por correo ===
try:
    enviar_reporte_por_correo(correo, rpa, capturas, timestamp)
    print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")
    sys.exit(1)
