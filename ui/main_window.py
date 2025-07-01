import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea,
    QHBoxLayout, QPushButton, QMessageBox
)
from ui.rpa_section import crear_seccion_rpa
from ui.email_section import crear_seccion_email
from ui.schedule_section import crear_seccion_schedule
from ui.buttons_section import conectar_botones_accion
from ui.config_loader import agregar_botones_carga
from constants import PLANTILLA_HTML_POR_DEFECTO


class RPAConfigUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de configuración RPA")
        self.resize(900, 750)

        self.config = {
            "rpa": {},
            "correo": {},
            "programacion": {}
        }

        self.url_routes = []

        # === Layout principal ===
        central = QWidget()
        self.central_layout = QVBoxLayout(central)

        # Botones para cargar configuración
        agregar_botones_carga(self)

        # Scroll principal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        # Secciones principales
        self.rpa_group = crear_seccion_rpa(self)
        self.scroll_layout.addWidget(self.rpa_group)

        self.correo_group = crear_seccion_email(self)
        self.scroll_layout.addWidget(self.correo_group)

        self.schedule_group = crear_seccion_schedule(self)
        self.scroll_layout.addWidget(self.schedule_group)

        # Botones inferiores
        botones_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar JSON")
        self.test_button = QPushButton("Test")
        self.deploy_button = QPushButton("Deploy")
        botones_layout.addWidget(self.save_button)
        botones_layout.addWidget(self.test_button)
        botones_layout.addWidget(self.deploy_button)
        self.scroll_layout.addLayout(botones_layout)
        self.scroll_layout.addStretch(1)

        scroll_content.setLayout(self.scroll_layout)
        scroll.setWidget(scroll_content)
        self.central_layout.addWidget(scroll)
        self.setCentralWidget(central)

        conectar_botones_accion(self)

    def update_auth_fields(self, auth_type: str):
        is_form = auth_type == "form_js"
        self.selector_user.setVisible(is_form)
        self.valor_user.setVisible(is_form)
        self.selector_pass.setVisible(is_form)
        self.valor_pass.setVisible(is_form)

        self.basic_user.setVisible(not is_form)
        self.basic_pass.setVisible(not is_form)

    def update_smtp_fields(self, selected: str):
        if selected == "Remoto":
            self.smtp_stack.setCurrentWidget(self.smtp_remoto_widget)
        else:
            self.smtp_stack.setCurrentWidget(self.smtp_local_widget)

    def obtener_config_desde_ui(self):
        required_attrs = [
            "nombre_rpa", "smtp_local_host", "smtp_local_port", "smtp_remoto_host", "smtp_remoto_port",
            "cred_remoto", "remitente", "destinatarios", "incluir_fecha", "cuerpo_html",
            "valor_user", "valor_pass", "basic_user", "basic_pass"
        ]
        for attr in required_attrs:
            if not hasattr(self, attr):
                raise AttributeError(f"Falta el campo requerido: {attr}")

        # === URLs ===
        urls_config = []
        for idx, w in enumerate(self.url_routes):
            url = w.url_input.text().strip()
            wait = int(w.wait_time_input.value())
            if idx == 0 and not url:
                raise ValueError("La URL de acceso inicial es obligatoria.")
            if url:
                urls_config.append({"url": url, "wait_time_ms": wait})

        # === Autenticación ===
        if self.tipo_auth.currentText() == "form_js":
            form_user_selector = self.selector_user.text().strip()
            form_user_value = self.valor_user.text().strip()
            form_pass_selector = self.selector_pass.text().strip()
            form_pass_value = self.valor_pass.text().strip()
            http_user = ""
            http_pass = ""
        else:
            form_user_selector = "#username"
            form_user_value = ""
            form_pass_selector = "#password"
            form_pass_value = ""
            http_user = self.basic_user.text().strip()
            http_pass = self.basic_pass.text().strip()

        # === Pantalla ===
        pantalla = {
            "viewport_width": self.viewport_width.value(),
            "viewport_height": self.viewport_height.value(),
            "captura_pagina_completa": self.captura_completa.isChecked()
        }

        # === Correo ===
        usar_remoto = self.smtp_selector.currentText() == "Remoto"
        correo = {
            "usar_remoto": usar_remoto,
            "smtp_local": {
                "servidor": self.smtp_local_host.text().strip(),
                "puerto": int(self.smtp_local_port.text() or 25)
            },
            "smtp_remoto": {
                "servidor": self.smtp_remoto_host.text().strip(),
                "puerto": int(self.smtp_remoto_port.text() or 587),
                "usuario": self.remitente.text().strip(),
                "clave_aplicacion": self.cred_remoto.text().strip()
            },
            "remitente": self.remitente.text().strip(),
            "destinatarios": [x.strip() for x in self.destinatarios.text().split(",") if x.strip()],
            "cc": [x.strip() for x in self.cc.text().split(",") if x.strip()],
            "asunto": self.asunto.text().strip(),
            "incluir_fecha": self.incluir_fecha.isChecked(),
            "cuerpo_html": self.cuerpo_html.toPlainText() or PLANTILLA_HTML_POR_DEFECTO
        }

        # === Programación ===
        programacion = {
            "frecuencia": self.frecuencia.currentText(),
            "intervalo": int(self.intervalo.text()),
            "hora_inicio": self.hora_inicio.text().strip()
        }

        # === Config final ===
        return {
            "rpa": {
                "nombre": self.nombre_rpa.text().strip(),
                "modo_navegador_visible": self.modo_visible.isChecked(),
                "tipo_autenticacion": self.tipo_auth.currentText(),
                "url_ruta": urls_config,
                "form_js": {
                    "username_selector": form_user_selector,
                    "username_value": form_user_value,
                    "password_selector": form_pass_selector,
                    "password_value": form_pass_value,
                    "login_action": "Enter"
                },
                "http_basic": {
                    "username": http_user,
                    "password": http_pass
                },
                "pantalla": pantalla
            },
            "correo": correo,
            "programacion": programacion
        }