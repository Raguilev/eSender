import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea,
    QHBoxLayout, QPushButton, QMessageBox
)
from ui.rpa_section import crear_seccion_rpa
from ui.email_section import crear_seccion_email
from ui.schedule_section import crear_seccion_schedule
from ui.buttons_section import conectar_botones_accion
from ui.config_loader import agregar_botones_carga, calcular_hash_config
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
        self.save_button.setVisible(False)  # Oculto inicialmente
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
        self.last_saved_path = None
        self.last_config_hash = None  # Para detectar si se modificó la configuración

        self.timer_actualizacion = self.startTimer(1000)

    def timerEvent(self, event):
        try:
            actual = self.obtener_config_desde_ui()
            actual_hash = calcular_hash_config(actual)
            self.save_button.setVisible(actual_hash != self.last_config_hash)
        except Exception:
            self.save_button.setVisible(False)

    def nuevo_rpa(self):
        from widgets.url_route_widget import URLRouteWidget

        self.nombre_rpa.clear()
        self.modo_visible.setChecked(False)
        self.viewport_width.setValue(1920)
        self.viewport_height.setValue(1080)
        self.captura_completa.setChecked(True)

        for w in self.url_routes:
            w.setParent(None)
        self.url_routes.clear()
        w = URLRouteWidget()
        self.url_routes.append(w)
        self.urls_list.addWidget(w)
        w.delete_btn.setDisabled(True)

        self.smtp_selector.setCurrentText("Local")
        self.update_smtp_fields("Local")
        self.smtp_local_host.clear()
        self.smtp_local_port.setText("25")
        self.smtp_remoto_host.clear()
        self.smtp_remoto_port.setText("587")
        self.cred_remoto.clear()
        self.smtp_remoto_user.clear()
        self.remitente.clear()
        self.destinatarios.clear()
        self.cc.clear()
        self.asunto.clear()
        self.incluir_fecha.setChecked(True)
        self.cuerpo_html.setPlainText(PLANTILLA_HTML_POR_DEFECTO)

        self.frecuencia.setCurrentText("daily")
        self.intervalo.setText("1")
        self.hora_inicio.setText("00:00")

        self.last_config_hash = calcular_hash_config(self.obtener_config_desde_ui())

    def update_smtp_fields(self, selected: str):
        if selected == "Remoto":
            self.smtp_stack.setCurrentWidget(self.smtp_remoto_widget)
        else:
            self.smtp_stack.setCurrentWidget(self.smtp_local_widget)

    def obtener_config_desde_ui(self):
        from widgets.url_route_widget import URLRouteWidget

        required_attrs = [
            "nombre_rpa", "smtp_local_host", "smtp_local_port", "smtp_remoto_host", "smtp_remoto_port",
            "cred_remoto", "remitente", "destinatarios", "cuerpo_html"
        ]
        for attr in required_attrs:
            if not hasattr(self, attr):
                raise AttributeError(f"Falta el campo requerido: {attr}")

        urls_config = []
        for idx, w in enumerate(self.url_routes):
            data = w.get_data()
            if idx == 0 and not data["url"]:
                raise ValueError("La URL de acceso inicial es obligatoria.")
            urls_config.append(data)

        pantalla = {
            "viewport_width": self.viewport_width.value(),
            "viewport_height": self.viewport_height.value(),
            "captura_pagina_completa": self.captura_completa.isChecked()
        }

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
                "usuario": self.smtp_remoto_user.text().strip(),
                "clave_aplicacion": self.cred_remoto.text().strip()
            },
            "remitente": self.remitente.text().strip(),
            "destinatarios": [x.strip() for x in self.destinatarios.text().split(",") if x.strip()],
            "cc": [x.strip() for x in self.cc.text().split(",") if x.strip()],
            "asunto": self.asunto.text().strip(),
            "incluir_fecha": self.incluir_fecha.isChecked(),
            "cuerpo_html": self.cuerpo_html.toPlainText() or PLANTILLA_HTML_POR_DEFECTO
        }

        programacion = {
            "frecuencia": self.frecuencia.currentText(),
            "intervalo": int(self.intervalo.text()),
            "hora_inicio": self.hora_inicio.text().strip()
        }

        return {
            "rpa": {
                "nombre": self.nombre_rpa.text().strip(),
                "modo_navegador_visible": self.modo_visible.isChecked(),
                "pantalla": pantalla,
                "url_ruta": urls_config
            },
            "correo": correo,
            "programacion": programacion
        }

    def set_config(self, data):
        from widgets.url_route_widget import URLRouteWidget

        rpa = data.get("rpa", {})
        self.nombre_rpa.setText(rpa.get("nombre", ""))
        self.modo_visible.setChecked(rpa.get("modo_navegador_visible", False))

        pantalla = rpa.get("pantalla", {})
        self.viewport_width.setValue(pantalla.get("viewport_width", 1920))
        self.viewport_height.setValue(pantalla.get("viewport_height", 1080))
        self.captura_completa.setChecked(pantalla.get("captura_pagina_completa", True))

        for w in self.url_routes:
            w.setParent(None)
        self.url_routes.clear()

        for i, ruta in enumerate(rpa.get("url_ruta", [])):
            w = URLRouteWidget(ruta_config=ruta)
            self.url_routes.append(w)
            self.urls_list.addWidget(w)
            if i == 0:
                w.delete_btn.setDisabled(True)

        correo = data.get("correo", {})
        usar_remoto = correo.get("usar_remoto", False)
        self.smtp_selector.setCurrentText("Remoto" if usar_remoto else "Local")
        self.update_smtp_fields("Remoto" if usar_remoto else "Local")

        self.smtp_local_host.setText(correo.get("smtp_local", {}).get("servidor", ""))
        self.smtp_local_port.setText(str(correo.get("smtp_local", {}).get("puerto", 25)))
        self.smtp_remoto_host.setText(correo.get("smtp_remoto", {}).get("servidor", ""))
        self.smtp_remoto_port.setText(str(correo.get("smtp_remoto", {}).get("puerto", 587)))
        self.cred_remoto.setText(correo.get("smtp_remoto", {}).get("clave_aplicacion", ""))
        self.smtp_remoto_user.setText(correo.get("smtp_remoto", {}).get("usuario", ""))
        self.remitente.setText(correo.get("remitente", ""))
        self.destinatarios.setText(", ".join(correo.get("destinatarios", [])))
        self.cc.setText(", ".join(correo.get("cc", [])))
        self.asunto.setText(correo.get("asunto", ""))
        self.incluir_fecha.setChecked(correo.get("incluir_fecha", True))
        self.cuerpo_html.setPlainText(correo.get("cuerpo_html", ""))

        prog = data.get("programacion", {})
        self.frecuencia.setCurrentText(prog.get("frecuencia", "daily"))
        self.intervalo.setText(str(prog.get("intervalo", 1)))
        self.hora_inicio.setText(prog.get("hora_inicio", "00:00"))

        self.last_config_hash = calcular_hash_config(data)