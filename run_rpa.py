import os
import sys
import json
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, "rpa_runner"))

from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo


def cargar_configuracion(ruta: str) -> dict:
    """
    Carga un archivo JSON de configuración.
    Finaliza si hay errores de lectura o formato.
    """
    if not os.path.isfile(ruta):
        print(f"[ERROR] Archivo de configuración no encontrado: {ruta}")
        sys.exit(1)

    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Fallo al leer la configuración JSON:\n{e}")
        sys.exit(1)


def validar_configuracion(config: dict):
    """
    Verifica campos mínimos requeridos para ejecutar el RPA de forma segura.
    """
    rpa = config.get("rpa", {})
    correo = config.get("correo", {})

    if not rpa.get("url_ruta") or not rpa["url_ruta"][0].get("url"):
        print("[ERROR] Se requiere al menos una URL de acceso inicial.")
        sys.exit(1)

    if correo.get("usar_remoto"):
        smtp = correo.get("smtp_remoto", {})
        if not smtp.get("usuario") or not smtp.get("clave_aplicacion"):
            print("[ERROR] Faltan credenciales para el servidor SMTP remoto.")
            sys.exit(1)
    else:
        smtp = correo.get("smtp_local", {})
        if not smtp.get("servidor"):
            print("[ADVERTENCIA] No se especificó un servidor SMTP local.")


def main():
    # === Verificar argumentos ===
    if len(sys.argv) < 2:
        print("Uso: run_rpa.py <ruta_config.json>")
        sys.exit(1)

    config_path = sys.argv[1]
    config = cargar_configuracion(config_path)
    validar_configuracion(config)

    rpa = config["rpa"]
    correo = config["correo"]

    # === Ejecutar navegación RPA ===
    try:
        capturas, timestamp = ejecutar_navegacion(rpa)
        print(f"[INFO] Se generaron {len(capturas)} capturas:")
        for idx, (url, path) in enumerate(capturas, start=1):
            print(f"  [{idx}] {url} -> {path}")
    except Exception as e:
        print(f"[ERROR] Fallo durante la navegación:\n{e}")
        sys.exit(1)

    # === Enviar reporte por correo ===
    try:
        enviar_reporte_por_correo(correo, rpa, capturas, timestamp)
        print("[INFO] Correo enviado correctamente.")
    except Exception as e:
        print(f"[ERROR] Fallo al enviar el correo:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()