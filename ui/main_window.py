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

        # Config base en memoria
        self.config = {
            "rpa": {},
            "correo": {},
            "programacion": {}
        }

        self.url_routes = []  # Lista de widgets dinámicos para URLs

        # === Layout principal ===
        central = QWidget()
        self.central_layout = QVBoxLayout(central)

        # Botones de carga/guardar configuración
        agregar_botones_carga(self)

        # Scroll de contenido
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

        # === Botones finales ===
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

        # Conectar lógica a botones y comboboxes
        conectar_botones_accion(self)

    def update_auth_fields(self, auth_type: str):
        """Alterna entre campos de login form_js y http_basic."""
        is_form = auth_type == "form_js"
        self.selector_user.setVisible(is_form)
        self.valor_user.setVisible(is_form)
        self.selector_pass.setVisible(is_form)
        self.valor_pass.setVisible(is_form)

        self.basic_user.setVisible(not is_form)
        self.basic_pass.setVisible(not is_form)

    def update_smtp_fields(self, selected: str):
        """Muestra el widget de SMTP correspondiente usando QStackedWidget."""
        if selected == "Remoto":
            self.smtp_stack.setCurrentWidget(self.smtp_remoto_widget)
        else:
            self.smtp_stack.setCurrentWidget(self.smtp_local_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RPAConfigUI()
    window.show()
    sys.exit(app.exec_())