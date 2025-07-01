import os
import json
import glob
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from jsonschema import validate, ValidationError
from constants import PLANTILLA_HTML_POR_DEFECTO, RUTA_CONFIG_PRINCIPAL, RUTA_CARPETA_RESPALDOS, SCHEMA_FILE

def agregar_botones_carga(parent):
    from PyQt5.QtWidgets import QHBoxLayout, QPushButton
    layout = QHBoxLayout()
    btn_ultima = QPushButton("Cargar última configuración")
    btn_abrir = QPushButton("Abrir configuración...")
    btn_ultima.clicked.connect(lambda: cargar_ultima_config(parent))
    btn_abrir.clicked.connect(lambda: seleccionar_archivo_config(parent))
    layout.addWidget(btn_ultima)
    layout.addWidget(btn_abrir)
    parent.central_layout.addLayout(layout)

def cargar_ultima_config(parent):
    os.makedirs(RUTA_CARPETA_RESPALDOS, exist_ok=True)
    archivos = glob.glob(os.path.join(RUTA_CARPETA_RESPALDOS, "*.json"))
    if not archivos:
        if os.path.exists(RUTA_CONFIG_PRINCIPAL):
            cargar_desde_archivo(parent, RUTA_CONFIG_PRINCIPAL)
        else:
            QMessageBox.warning(parent, "No encontrado", "No hay configuraciones guardadas.")
        return
    ultimo = max(archivos, key=os.path.getmtime)
    cargar_desde_archivo(parent, ultimo)

def seleccionar_archivo_config(parent):
    os.makedirs(RUTA_CARPETA_RESPALDOS, exist_ok=True)
    archivo, _ = QFileDialog.getOpenFileName(parent, "Seleccionar configuración", RUTA_CARPETA_RESPALDOS, "Archivos JSON (*.json)")
    if archivo:
        cargar_desde_archivo(parent, archivo)

def cargar_desde_archivo(parent, ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        aplicar_datos_config(parent, data)
        QMessageBox.information(parent, "Configuración cargada", f"Se cargó la configuración desde:\n{ruta}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo cargar la configuración:\n{e}")

def aplicar_datos_config(parent, data):
    rpa = data.get("rpa", {})
    parent.nombre_rpa.setText(rpa.get("nombre", ""))
    parent.tipo_auth.setCurrentText(rpa.get("tipo_autenticacion", "form_js"))
    parent.modo_visible.setChecked(rpa.get("modo_navegador_visible", False))

    if rpa.get("tipo_autenticacion") == "form_js":
        parent.auth_user.setText(f"{rpa.get('form_js', {}).get('username_selector', '')}:{rpa.get('form_js', {}).get('username_value', '')}")
        parent.auth_pass.setText(f"{rpa.get('form_js', {}).get('password_selector', '')}:{rpa.get('form_js', {}).get('password_value', '')}")
    else:
        parent.auth_user.setText(rpa.get("http_basic", {}).get("username", ""))
        parent.auth_pass.setText(rpa.get("http_basic", {}).get("password", ""))

    pantalla = rpa.get("pantalla", {})
    parent.viewport_width.setValue(pantalla.get("viewport_width", 1920))
    parent.viewport_height.setValue(pantalla.get("viewport_height", 1080))
    parent.captura_completa.setChecked(pantalla.get("captura_pagina_completa", True))

    for widget in parent.url_routes[:]:
        parent.urls_list.removeWidget(widget)
        widget.setParent(None)
        parent.url_routes.remove(widget)

    url_ruta = rpa.get("url_ruta", [])
    for idx, ruta in enumerate(url_ruta):
        from ui.rpa_section import add_url_widget
        add_url_widget(parent, is_initial=(idx == 0))
        parent.url_routes[-1].url_input.setText(ruta.get("url", ""))
        parent.url_routes[-1].wait_time_input.setValue(int(ruta.get("wait_time_ms", 10000)))
    if not url_ruta:
        from ui.rpa_section import add_url_widget
        add_url_widget(parent, is_initial=True)

    correo = data.get("correo", {})
    parent.smtp_selector.setCurrentText("Remoto" if correo.get("usar_remoto") else "Local")
    parent.remitente.setText(correo.get("remitente", ""))
    parent.destinatarios.setText(", ".join(correo.get("destinatarios", [])))
    parent.cc.setText(", ".join(correo.get("cc", [])))
    parent.asunto.setText(correo.get("asunto", ""))
    parent.incluir_fecha.setChecked(correo.get("incluir_fecha", False))
    parent.cuerpo_html.setPlainText(correo.get("cuerpo_html", ""))

    parent.smtp_local_host.setText(correo.get("smtp_local", {}).get("servidor", ""))
    parent.smtp_local_port.setText(str(correo.get("smtp_local", {}).get("puerto", "")))
    parent.smtp_remoto_host.setText(correo.get("smtp_remoto", {}).get("servidor", ""))
    parent.smtp_remoto_port.setText(str(correo.get("smtp_remoto", {}).get("puerto", "")))
    parent.cred_remoto.setText(correo.get("smtp_remoto", {}).get("clave_aplicacion", ""))

    prog = data.get("programacion", {})
    parent.frecuencia.setCurrentText(prog.get("frecuencia", "hourly"))
    parent.intervalo.setText(str(prog.get("intervalo", 6)))
    parent.hora_inicio.setText(prog.get("hora_inicio", "00:00"))

def save_config(parent):
    try:
        urls_config = []
        for idx, w in enumerate(parent.url_routes):
            url = w.url_input.text().strip()
            wait = int(w.wait_time_input.value())
            if idx == 0 and not url:
                raise ValueError("La URL de acceso inicial es obligatoria.")
            if url:
                urls_config.append({"url": url, "wait_time_ms": wait})

        form_user_selector, form_user_value = parent.auth_user.text().split(":", 1) if ":" in parent.auth_user.text() else ("#username", parent.auth_user.text())
        form_pass_selector, form_pass_value = parent.auth_pass.text().split(":", 1) if ":" in parent.auth_pass.text() else ("#password", parent.auth_pass.text())

        parent.config["rpa"] = {
            "nombre": parent.nombre_rpa.text(),
            "modo_navegador_visible": parent.modo_visible.isChecked(),
            "tipo_autenticacion": parent.tipo_auth.currentText(),
            "url_ruta": urls_config,
            "form_js": {
                "username_selector": form_user_selector,
                "username_value": form_user_value,
                "password_selector": form_pass_selector,
                "password_value": form_pass_value,
                "login_action": "Enter"
            },
            "http_basic": {
                "username": parent.auth_user.text() if parent.tipo_auth.currentText() == "http_basic" else "",
                "password": parent.auth_pass.text() if parent.tipo_auth.currentText() == "http_basic" else ""
            },
            "pantalla": {
                "viewport_width": parent.viewport_width.value(),
                "viewport_height": parent.viewport_height.value(),
                "captura_pagina_completa": parent.captura_completa.isChecked()
            }
        }

        parent.config["correo"] = {
            "usar_remoto": parent.smtp_selector.currentText() == "Remoto",
            "smtp_local": {
                "servidor": parent.smtp_local_host.text(),
                "puerto": int(parent.smtp_local_port.text())
            },
            "smtp_remoto": {
                "servidor": parent.smtp_remoto_host.text(),
                "puerto": int(parent.smtp_remoto_port.text()),
                "usuario": parent.remitente.text(),
                "clave_aplicacion": parent.cred_remoto.text()
            },
            "remitente": parent.remitente.text(),
            "destinatarios": [x.strip() for x in parent.destinatarios.text().split(",") if x.strip()],
            "cc": [x.strip() for x in parent.cc.text().split(",") if x.strip()],
            "asunto": parent.asunto.text(),
            "incluir_fecha": parent.incluir_fecha.isChecked(),
            "cuerpo_html": parent.cuerpo_html.toPlainText() or PLANTILLA_HTML_POR_DEFECTO
        }

        parent.config["programacion"] = {
            "frecuencia": parent.frecuencia.currentText(),
            "intervalo": int(parent.intervalo.text()),
            "hora_inicio": parent.hora_inicio.text()
        }

        with open(SCHEMA_FILE, encoding="utf-8") as f:
            schema = json.load(f)
            validate(instance=parent.config, schema=schema)

        nombre_rpa = parent.config["rpa"].get("nombre", "rpa_email").replace(" ", "_")
        ruta_json = os.path.join(".", f"{nombre_rpa}.json")

        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(parent.config, f, indent=4, ensure_ascii=False)

        os.makedirs(RUTA_CARPETA_RESPALDOS, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        respaldo = os.path.join(RUTA_CARPETA_RESPALDOS, f"{nombre_rpa}_{timestamp}.json")
        shutil.copyfile(ruta_json, respaldo)

        QMessageBox.information(parent, "Éxito", f"Configuración guardada en {ruta_json}")
        return ruta_json

    except ValidationError as ve:
        path = " → ".join(str(p) for p in ve.path)
        QMessageBox.critical(parent, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"No se pudo guardar: {e}")