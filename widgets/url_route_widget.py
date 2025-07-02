from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QSizePolicy, QComboBox, QStackedWidget, QFormLayout, QCheckBox
)


class URLRouteWidget(QWidget):
    def __init__(self, url_text='', wait_time=10000, capturar=True, ruta_config=None, parent=None):
        super().__init__(parent)

        # === Layout principal vertical ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)

        # === Fila superior: URL + Espera + Captura + Eliminar ===
        top_layout = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://servidor.com/ruta")
        self.url_input.setText(url_text)
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.url_input.setToolTip("Ingrese la URL que debe visitar el RPA")

        self.wait_time_input = QSpinBox()
        self.wait_time_input.setRange(1000, 300000)
        self.wait_time_input.setSingleStep(1000)
        self.wait_time_input.setValue(wait_time)
        self.wait_time_input.setSuffix(" ms")
        self.wait_time_input.setToolTip("Tiempo de espera antes de continuar (en milisegundos)")

        self.capture_checkbox = QCheckBox("Capturar")
        self.capture_checkbox.setChecked(capturar)
        self.capture_checkbox.setToolTip("Capturar pantalla tras visitar esta URL")

        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.setToolTip("Eliminar esta URL de la secuencia")

        top_layout.addWidget(QLabel("URL:"))
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(QLabel("Espera:"))
        top_layout.addWidget(self.wait_time_input)
        top_layout.addWidget(self.capture_checkbox)
        top_layout.addWidget(self.delete_btn)

        self.main_layout.addLayout(top_layout)

        # === Combo de autenticación ===
        self.auth_mode_combo = QComboBox()
        self.auth_mode_combo.addItems([
            "Sin autenticación",
            "Autenticación HTTP Basic",
            "Autenticación Form JS"
        ])
        self.auth_mode_combo.setToolTip("Seleccione si esta URL necesita autenticación")
        self.auth_mode_combo.currentIndexChanged.connect(self.update_auth_visibility)
        self.main_layout.addWidget(self.auth_mode_combo)

        # === Stack de autenticación dinámico ===
        self.auth_stack = QStackedWidget()

        # Página 0: Sin autenticación
        self.auth_stack.addWidget(QWidget())

        # Página 1: HTTP Basic
        self.basic_widget = QWidget()
        basic_layout = QFormLayout(self.basic_widget)
        self.basic_user = QLineEdit()
        self.basic_user.setPlaceholderText("Ej: admin")
        self.basic_user.setToolTip("Usuario para autenticación HTTP Basic")
        self.basic_pass = QLineEdit()
        self.basic_pass.setPlaceholderText("Contraseña")
        self.basic_pass.setToolTip("Contraseña para autenticación HTTP Basic")
        self.basic_pass.setEchoMode(QLineEdit.Password)
        basic_layout.addRow("Usuario:", self.basic_user)
        basic_layout.addRow("Contraseña:", self.basic_pass)
        self.auth_stack.addWidget(self.basic_widget)

        # Página 2: Form JS
        self.formjs_widget = QWidget()
        formjs_layout = QFormLayout(self.formjs_widget)

        self.form_user_value = QLineEdit()
        self.form_user_value.setPlaceholderText("Ej: admin")
        self.form_user_value.setToolTip("Valor del campo usuario en el formulario")

        self.form_pass_value = QLineEdit()
        self.form_pass_value.setPlaceholderText("Ej: ********")
        self.form_pass_value.setToolTip("Valor del campo contraseña en el formulario")
        self.form_pass_value.setEchoMode(QLineEdit.Password)

        self.toggle_selectores = QCheckBox("Editar selectores")
        self.toggle_selectores.setChecked(False)
        self.toggle_selectores.stateChanged.connect(self.toggle_selectores_visibility)

        self.selectores_widget = QWidget()
        selectores_layout = QFormLayout(self.selectores_widget)

        self.form_user_selector = QLineEdit()
        self.form_user_selector.setPlaceholderText("Ej: #usuario")
        self.form_user_selector.setToolTip("Selector del campo usuario")

        self.form_pass_selector = QLineEdit()
        self.form_pass_selector.setPlaceholderText("Ej: #clave")
        self.form_pass_selector.setToolTip("Selector del campo contraseña")

        selectores_layout.addRow("Selector usuario:", self.form_user_selector)
        selectores_layout.addRow("Selector contraseña:", self.form_pass_selector)
        self.selectores_widget.setVisible(False)

        formjs_layout.addRow("Usuario:", self.form_user_value)
        formjs_layout.addRow("Contraseña:", self.form_pass_value)
        formjs_layout.addRow(self.toggle_selectores)
        formjs_layout.addRow(self.selectores_widget)

        self.auth_stack.addWidget(self.formjs_widget)

        self.auth_stack.setVisible(False)
        self.main_layout.addWidget(self.auth_stack)

        # Si se proporciona una configuración previa, restaurarla
        if ruta_config:
            self.restore_config(ruta_config)

    def update_auth_visibility(self, index):
        self.auth_stack.setVisible(index != 0)
        self.auth_stack.setCurrentIndex(index)

    def toggle_selectores_visibility(self, state):
        self.selectores_widget.setVisible(state == 2)

    def get_data(self):
        data = {
            "url": self.url_input.text().strip(),
            "wait_time_ms": self.wait_time_input.value(),
            "capturar": self.capture_checkbox.isChecked(),
            "requiere_autenticacion": self.auth_mode_combo.currentIndex() != 0
        }

        if data["requiere_autenticacion"]:
            index = self.auth_mode_combo.currentIndex()
            if index == 1:
                data["tipo_autenticacion"] = "http_basic"
                data["http_basic"] = {
                    "username": self.basic_user.text().strip(),
                    "password": self.basic_pass.text()
                }
            elif index == 2:
                data["tipo_autenticacion"] = "form_js"
                data["form_js"] = {
                    "username_value": self.form_user_value.text().strip(),
                    "password_value": self.form_pass_value.text(),
                    "username_selector": self.form_user_selector.text().strip(),
                    "password_selector": self.form_pass_selector.text().strip(),
                    "login_action": "ENTER"
                }

        return data

    def restore_config(self, ruta_config):
        self.url_input.setText(ruta_config.get("url", ""))
        self.wait_time_input.setValue(ruta_config.get("wait_time_ms", 10000))
        self.capture_checkbox.setChecked(ruta_config.get("capturar", True))

        requiere_auth = ruta_config.get("requiere_autenticacion", False)
        if not requiere_auth:
            self.auth_mode_combo.setCurrentIndex(0)
        else:
            tipo = ruta_config.get("tipo_autenticacion", "")
            if tipo == "http_basic":
                self.auth_mode_combo.setCurrentIndex(1)
                self.basic_user.setText(ruta_config.get("http_basic", {}).get("username", ""))
                self.basic_pass.setText(ruta_config.get("http_basic", {}).get("password", ""))
            elif tipo == "form_js":
                self.auth_mode_combo.setCurrentIndex(2)
                form_js = ruta_config.get("form_js", {})
                self.form_user_value.setText(form_js.get("username_value", ""))
                self.form_pass_value.setText(form_js.get("password_value", ""))
                user_sel = form_js.get("username_selector", "")
                pass_sel = form_js.get("password_selector", "")
                self.toggle_selectores.setChecked(bool(user_sel or pass_sel))
                self.form_user_selector.setText(user_sel)
                self.form_pass_selector.setText(pass_sel)