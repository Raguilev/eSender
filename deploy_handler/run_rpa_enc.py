import os
import sys
from datetime import datetime

# === Asegurar acceso al runner incluso desde .exe ===
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, "rpa_runner"))

from decryptor import descifrar_configuracion
from rpa_runner.navigation import ejecutar_navegacion
from rpa_runner.mailer import enviar_reporte_por_correo


def validar_configuracion(config: dict):
    """
    Valida campos mínimos requeridos en la configuración.
    Termina el programa si hay errores críticos.
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
    if len(sys.argv) < 3:
        print("Uso: run_rpa_enc.py <ruta_config.enc> <ruta_key.key>")
        sys.exit(1)

    ruta_enc, ruta_key = sys.argv[1], sys.argv[2]

    if not os.path.isfile(ruta_enc) or not os.path.isfile(ruta_key):
        print("[ERROR] Archivo .enc o .key no encontrado.")
        sys.exit(1)

    # === Descifrar configuración ===
    try:
        config = descifrar_configuracion(ruta_enc, ruta_key)
    except Exception as e:
        print(f"[ERROR] Fallo al descifrar la configuración:\n{e}")
        sys.exit(1)

    # === Validar campos clave ===
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