import os
from datetime import datetime
from playwright.sync_api import sync_playwright

def ejecutar_navegacion(rpa_config, screenshot_dir="Reportes"):
    url_rutas = rpa_config.get("url_ruta", [])
    if not url_rutas:
        raise ValueError("No se encontraron rutas de navegación.")

    os.makedirs(screenshot_dir, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    safe_timestamp = now.strftime("%Y-%m-%d_%H-%M-%S") if rpa_config.get("modo_navegador_visible") else "headless"

    capturas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not rpa_config.get("modo_navegador_visible", False),
            args=["--ignore-certificate-errors"]
        )

        for idx, ruta in enumerate(url_rutas):
            url_actual = ruta.get("url")
            wait_time = int(ruta.get("wait_time_ms", 0))
            capturar = ruta.get("capturar", False)
            requiere_auth = ruta.get("requiere_autenticacion", False)

            if not url_actual:
                raise ValueError(f"URL vacía en la posición {idx + 1}")

            # Preparar argumentos para el contexto
            context_args = {
                "viewport": {
                    "width": rpa_config.get("pantalla", {}).get("viewport_width", 1920),
                    "height": rpa_config.get("pantalla", {}).get("viewport_height", 1080)
                },
                "ignore_https_errors": True
            }

            # Autenticación HTTP BASIC (solo si aplica para esta URL)
            if requiere_auth and ruta.get("tipo_autenticacion") == "http_basic":
                creds = ruta.get("http_basic", {})
                if not creds.get("username") or not creds.get("password"):
                    raise ValueError(f"Credenciales http_basic vacías en URL {idx + 1}")
                context_args["http_credentials"] = {
                    "username": creds["username"],
                    "password": creds["password"]
                }

            with browser.new_context(**context_args) as context:
                page = context.new_page()

                print(f"[{idx+1}] Navegando a: {url_actual}")
                page.goto(url_actual, timeout=60000)

                # Autenticación FORM_JS (solo si aplica para esta URL)
                if requiere_auth and ruta.get("tipo_autenticacion") == "form_js":
                    form = ruta.get("form_js", {})
                    if not form.get("username_value") or not form.get("password_value"):
                        raise ValueError(f"Credenciales form_js vacías en URL {idx + 1}")

                    page.fill(form.get("username_selector", "#username"), form["username_value"])
                    page.fill(form.get("password_selector", "#password"), form["password_value"])
                    page.keyboard.press("Enter")

                if wait_time > 0:
                    print(f"Esperando {wait_time} ms...")
                    page.wait_for_timeout(wait_time)

                if capturar:
                    filename = f"captura_{idx+1}_{safe_timestamp}.png"
                    path = os.path.join(screenshot_dir, filename)
                    page.screenshot(
                        path=path,
                        full_page=rpa_config.get("pantalla", {}).get("captura_pagina_completa", True)
                    )
                    capturas.append((url_actual, path))
                    print(f"Captura tomada: {path}")

    return capturas, timestamp