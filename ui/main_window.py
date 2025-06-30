import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea,
    QHBoxLayout, QPushButton
)
from ui.rpa_section import crear_seccion_rpa
from ui.email_section import crear_seccion_email
from ui.schedule_section import crear_seccion_schedule
from ui.buttons_section import conectar_botones_accion
from ui.config_loader import agregar_botones_carga

class RPAConfigUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de configuración RPA")
        self.resize(900, 750)

        # Estructura interna del config (cargado y guardado como JSON)
        self.config = {
            "rpa": {},
            "correo": {},
            "programacion": {}
        }

        self.url_routes = []  # Lista de widgets URLRouteWidget agregados dinámicamente

        # Estructura principal
        central = QWidget()
        self.central_layout = QVBoxLayout(central)
        agregar_botones_carga(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        # Secciones configurables
        self.rpa_group = crear_seccion_rpa(self)
        self.scroll_layout.addWidget(self.rpa_group)

        self.correo_group = crear_seccion_email(self)
        self.scroll_layout.addWidget(self.correo_group)

        self.schedule_group = crear_seccion_schedule(self)
        self.scroll_layout.addWidget(self.schedule_group)

        # Botones finales
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

        # Conexión de acciones principales
        conectar_botones_accion(self)

    def update_auth_fields(self, auth_type):
        """Actualiza los placeholders de usuario y contraseña según tipo de autenticación."""
        if auth_type == "form_js":
            self.auth_user.setPlaceholderText("Selector + valor usuario (form_js)")
            self.auth_pass.setPlaceholderText("Selector + valor contraseña (form_js)")
        else:
            self.auth_user.setPlaceholderText("Usuario (http_basic)")
            self.auth_pass.setPlaceholderText("Contraseña (http_basic)")

    def update_smtp_fields(self, selected):
        """Actualiza campos de SMTP en base a si es remoto o local (usado por email_section)."""
        if selected == "Remoto":
            self.smtp_local.setDisabled(True)
            self.smtp_remoto.setDisabled(False)
            self.cred_remoto.setDisabled(False)
        else:
            self.smtp_local.setDisabled(False)
            self.smtp_remoto.setDisabled(True)
            self.cred_remoto.setDisabled(True)