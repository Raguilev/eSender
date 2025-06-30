import os
import json
import shutil
import glob
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout,
    QMessageBox, QGroupBox, QFormLayout, QComboBox, QStackedWidget,
    QSpinBox, QMainWindow, QSizePolicy, QScrollArea, QFileDialog
)
from deploy_handler import create_rpa_package
from jsonschema import validate, ValidationError
from PyQt5.QtCore import QProcess, Qt

PLANTILLA_HTML_POR_DEFECTO = """
<p>Estimado equipo,</p>
<p>Se ha generado correctamente el siguiente reporte automático desde la plataforma <b>{{nombre_rpa}}</b>.</p>
<p><b>Fecha y hora de captura:</b> {{fecha}}</p>
<p><b>Vista previa del panel:</b></p>
<img src="cid:screenshot" alt="Panel" />
<p><a href="{{url_dashboard}}" target="_blank">Ir al dashboard</a></p>
<br>
<p><small>Este mensaje fue generado automáticamente por el sistema de monitoreo. Por favor, no responder.</small></p>
"""

class URLRouteWidget(QWidget):
    def __init__(self, url_text='', wait_time=10000, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://servidor.com/ruta")
        self.url_input.setText(url_text)
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.wait_time_input = QSpinBox()
        self.wait_time_input.setRange(1000, 300000)
        self.wait_time_input.setSingleStep(1000)
        self.wait_time_input.setValue(wait_time)
        self.wait_time_input.setSuffix(" ms")
        self.delete_btn = QPushButton("Eliminar")
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input)
        layout.addWidget(QLabel("Espera:"))
        layout.addWidget(self.wait_time_input)
        layout.addWidget(self.delete_btn)
        self.setLayout(layout)

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
        self.file_path = "rpa_email.json"
        self.url_routes = []

        # --------- Main Widget con Scroll ---------
        central = QWidget()
        self.central_layout = QVBoxLayout(central)
        self.add_config_buttons()  # <-- Botones de configuración siempre arriba

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        # --------- Sección RPA ---------
        self.rpa_group = QGroupBox("Configuración RPA")
        self.rpa_form = QFormLayout()
        self.rpa_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.nombre_rpa = QLineEdit()
        self.nombre_rpa.setPlaceholderText("Ej: Monitoreo Principal")
        self.nombre_rpa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tipo_auth = QComboBox()
        self.tipo_auth.addItems(["form_js", "http_basic"])
        self.tipo_auth.currentTextChanged.connect(self.update_auth_fields)
        self.modo_visible = QCheckBox("Modo navegador Visible")
        self.rpa_form.addRow("Nombre RPA:", self.nombre_rpa)
        self.rpa_form.addRow("Tipo de autenticación:", self.tipo_auth)
        self.rpa_form.addRow(self.modo_visible)
        self.auth_user = QLineEdit()
        self.auth_pass = QLineEdit()
        self.auth_pass.setEchoMode(QLineEdit.Password)
        self.auth_user.setPlaceholderText("Usuario")
        self.auth_pass.setPlaceholderText("Contraseña")
        self.auth_user.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.auth_pass.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rpa_form.addRow("Usuario:", self.auth_user)
        self.rpa_form.addRow("Contraseña:", self.auth_pass)

        # Secuencia de URLs
        self.urls_group = QGroupBox("Secuencia de URLs a visitar")
        self.urls_layout = QVBoxLayout()
        self.urls_list = QVBoxLayout()
        self.urls_layout.addLayout(self.urls_list)
        self.add_url_btn = QPushButton("Añadir URL")
        self.add_url_btn.clicked.connect(self.add_url_widget)
        self.urls_layout.addWidget(self.add_url_btn)
        self.urls_group.setLayout(self.urls_layout)
        self.rpa_form.addRow(self.urls_group)
        self.rpa_group.setLayout(self.rpa_form)
        self.add_url_widget(is_initial=True)

        # --------- Sección Correo ---------
        self.correo_group = QGroupBox("Configuración de Correo")
        self.correo_form = QFormLayout()
        self.correo_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.smtp_selector = QComboBox()
        self.smtp_selector.addItems(["Local", "Remoto"])
        self.smtp_selector.currentTextChanged.connect(self.update_smtp_fields)
        self.correo_form.addRow("Proveedor SMTP:", self.smtp_selector)
        self.smtp_stack = QStackedWidget()
        self.smtp_local_widget = QWidget()
        local_layout = QFormLayout()
        self.smtp_local = QLineEdit()
        self.smtp_local.setPlaceholderText("servidor:puerto")
        self.smtp_local.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        local_layout.addRow("Servidor SMTP:", self.smtp_local)
        self.smtp_local_widget.setLayout(local_layout)
        self.smtp_remoto_widget = QWidget()
        remoto_layout = QFormLayout()
        self.smtp_remoto = QLineEdit()
        self.cred_remoto = QLineEdit()
        self.cred_remoto.setEchoMode(QLineEdit.Password)
        self.smtp_remoto.setPlaceholderText("smtp.server.com:puerto")
        self.cred_remoto.setPlaceholderText("Clave de aplicación")
        self.smtp_remoto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cred_remoto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        remoto_layout.addRow("Servidor SMTP:", self.smtp_remoto)
        remoto_layout.addRow("Clave Remota:", self.cred_remoto)
        self.smtp_remoto_widget.setLayout(remoto_layout)
        self.smtp_stack.addWidget(self.smtp_local_widget)
        self.smtp_stack.addWidget(self.smtp_remoto_widget)
        self.correo_form.addRow(self.smtp_stack)
        self.remitente = QLineEdit()
        self.remitente.setPlaceholderText("example@dominio.com")
        self.destinatarios = QLineEdit()
        self.destinatarios.setPlaceholderText("correo1@dominio.com, correo2@dominio.com")
        self.cc = QLineEdit()
        self.cc.setPlaceholderText("correoCC@dominio.com")
        self.asunto = QLineEdit()
        self.incluir_fecha = QCheckBox("Incluir fecha en asunto")
        self.cuerpo_html = QTextEdit()
        self.cuerpo_html.setPlainText(PLANTILLA_HTML_POR_DEFECTO)
        self.cuerpo_html.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.correo_form.addRow("Remitente:", self.remitente)
        self.correo_form.addRow("Destinatarios:", self.destinatarios)
        self.correo_form.addRow("CC:", self.cc)
        self.correo_form.addRow("Asunto:", self.asunto)
        self.correo_form.addRow(self.incluir_fecha)
        self.correo_form.addRow("Cuerpo HTML:", self.cuerpo_html)
        self.correo_group.setLayout(self.correo_form)

        # --------- Sección Programación ---------
        self.schedule_group = QGroupBox("Programación de tarea automatizada")
        self.schedule_form = QFormLayout()
        self.schedule_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.frecuencia = QComboBox()
        self.frecuencia.addItems(["hourly", "daily", "weekly"])
        self.intervalo = QLineEdit("6")
        self.hora_inicio = QLineEdit("00:00")
        self.schedule_form.addRow("Frecuencia:", self.frecuencia)
        self.schedule_form.addRow("Intervalo (ej. cada X horas/días):", self.intervalo)
        self.schedule_form.addRow("Hora de inicio (HH:MM):", self.hora_inicio)
        self.schedule_group.setLayout(self.schedule_form)

        # --------- Botones ---------
        self.save_button = QPushButton("Guardar JSON")
        self.save_button.clicked.connect(self.save_config)
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.run_test_rpa)
        self.deploy_button = QPushButton("Deploy")
        self.deploy_button.clicked.connect(self.deploy_rpa)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.deploy_button)

        # --------- Layout principal en Scroll ---------
        self.scroll_layout.addWidget(self.rpa_group)
        self.scroll_layout.addWidget(self.correo_group)
        self.scroll_layout.addWidget(self.schedule_group)
        self.scroll_layout.addLayout(button_layout)
        self.scroll_layout.addStretch(1)
        scroll_content.setLayout(self.scroll_layout)
        scroll.setWidget(scroll_content)
        self.central_layout.addWidget(scroll)
        self.setCentralWidget(central)

        self.update_auth_fields(self.tipo_auth.currentText())
        self.update_smtp_fields()

    def add_config_buttons(self):
        config_buttons_layout = QHBoxLayout()
        self.load_last_btn = QPushButton("Cargar última configuración")
        self.load_last_btn.clicked.connect(self.load_last_config)
        self.load_select_btn = QPushButton("Abrir configuración...")
        self.load_select_btn.clicked.connect(self.select_config_file)
        config_buttons_layout.addWidget(self.load_last_btn)
        config_buttons_layout.addWidget(self.load_select_btn)
        self.central_layout.addLayout(config_buttons_layout)

    def add_url_widget(self, is_initial=False):
        url_widget = URLRouteWidget(
            url_text="" if not is_initial else "",
            wait_time=10000 if not is_initial else 0
        )
        if not is_initial:
            url_widget.delete_btn.clicked.connect(lambda _, w=url_widget: self.remove_url_widget(w))
        else:
            url_widget.delete_btn.setDisabled(True)  # La primera URL no se puede eliminar
        self.urls_list.addWidget(url_widget)
        self.url_routes.append(url_widget)

    def remove_url_widget(self, widget):
        self.urls_list.removeWidget(widget)
        widget.setParent(None)
        self.url_routes.remove(widget)

    def update_auth_fields(self, auth_type):
        if auth_type == "form_js":
            self.auth_user.setPlaceholderText("Username form_js")
            self.auth_pass.setPlaceholderText("Password form_js")
        else:
            self.auth_user.setPlaceholderText("Username http_basic")
            self.auth_pass.setPlaceholderText("Password http_basic")

    def update_smtp_fields(self):
        if self.smtp_selector.currentText() == "Local":
            self.smtp_stack.setCurrentIndex(0)
        else:
            self.smtp_stack.setCurrentIndex(1)

    def save_config(self):
        try:
            smtp_local_host, smtp_local_port = self.smtp_local.text().split(":")
            smtp_remoto_host, smtp_remoto_port = self.smtp_remoto.text().split(":")
            urls_config = []
            for idx, w in enumerate(self.url_routes):
                url = w.url_input.text().strip()
                wait = int(w.wait_time_input.value())
                if idx == 0 and not url:
                    raise ValueError("La URL de acceso inicial es obligatoria.")
                urls_config.append({"url": url, "wait_time_ms": wait})
            self.config["rpa"] = {
                "nombre": self.nombre_rpa.text(),
                "modo_navegador_visible": self.modo_visible.isChecked(),
                "tipo_autenticacion": self.tipo_auth.currentText(),
                "url_ruta": urls_config,
                "form_js": {
                    "username_selector": "#username",
                    "username_value": self.auth_user.text() if self.tipo_auth.currentText() == "form_js" else "",
                    "password_selector": "#value",
                    "password_value": self.auth_pass.text() if self.tipo_auth.currentText() == "form_js" else "",
                    "login_action": "Enter"
                },
                "http_basic": {
                    "username": self.auth_user.text() if self.tipo_auth.currentText() == "http_basic" else "",
                    "password": self.auth_pass.text() if self.tipo_auth.currentText() == "http_basic" else ""
                },
                "esperas": {
                    "wait_time_after_login": 70000,
                    "wait_time_dashboard": 20000
                },
                "pantalla": {
                    "viewport_width": 1920,
                    "viewport_height": 1080,
                    "captura_pagina_completa": True
                }
            }
            self.config["correo"] = {
                "usar_remoto": self.smtp_selector.currentText() == "Remoto",
                "smtp_local": {
                    "servidor": smtp_local_host,
                    "puerto": int(smtp_local_port)
                },
                "smtp_remoto": {
                    "servidor": smtp_remoto_host,
                    "puerto": int(smtp_remoto_port),
                    "usuario": self.remitente.text(),
                    "clave_aplicacion": self.cred_remoto.text()
                },
                "remitente": self.remitente.text(),
                "destinatarios": [x.strip() for x in self.destinatarios.text().split(",") if x.strip()],
                "cc": [x.strip() for x in self.cc.text().split(",") if x.strip()],
                "asunto": self.asunto.text(),
                "incluir_fecha": self.incluir_fecha.isChecked(),
                "cuerpo_html": self.cuerpo_html.toPlainText() if self.cuerpo_html.toPlainText().strip() else PLANTILLA_HTML_POR_DEFECTO
            }
            self.config["programacion"] = {
                "frecuencia": self.frecuencia.currentText(),
                "intervalo": int(self.intervalo.text()),
                "hora_inicio": self.hora_inicio.text()
            }
            # Validar con schema
            with open("rpa_email.schema.json", encoding="utf-8") as schema_file:
                schema = json.load(schema_file)
                validate(instance=self.config, schema=schema)
            # Guardar config principal
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            # Guardar copia con timestamp
            folder = "configuraciones_guardadas"
            os.makedirs(folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_destino = os.path.join(folder, f"rpa_email_{timestamp}.json")
            shutil.copyfile(self.file_path, archivo_destino)
            QMessageBox.information(self, "Éxito", f"Configuración guardada en {self.file_path}")
        except ValidationError as ve:
            path = " → ".join(str(p) for p in ve.path)
            QMessageBox.critical(self, "Error de validación", f"Campo: {path}\nDetalle: {ve.message}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def run_test_rpa(self):
        self.process = QProcess(self)
        self.process.setProgram("python")
        self.process.setArguments(["main.py"])
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        self.process.start()

    def deploy_rpa(self):
        try:
            create_rpa_package(self.file_path)
            QMessageBox.information(self, "Deploy", "Se ha generado el paquete del RPA exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error durante el deploy: {e}")

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8")
        print("STDOUT:\n", stdout)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="replace")
        print("STDERR:\n", stderr)
        QMessageBox.critical(self, "Error al ejecutar el RPA", stderr)

    def load_last_config(self):
        folder = "configuraciones_guardadas"
        os.makedirs(folder, exist_ok=True)
        pattern = os.path.join(folder, "*.json")
        files = glob.glob(pattern)
        if not files:
            if os.path.exists(self.file_path):
                self.load_config_from_file(self.file_path)
            else:
                QMessageBox.warning(self, "No encontrado", "No hay configuraciones guardadas.")
            return
        last_file = max(files, key=os.path.getmtime)
        self.load_config_from_file(last_file)

    def select_config_file(self):
        folder = "configuraciones_guardadas"
        os.makedirs(folder, exist_ok=True)
        file, _ = QFileDialog.getOpenFileName(self, "Seleccionar configuración", folder, "Archivos JSON (*.json)")
        if file:
            self.load_config_from_file(file)

    def load_config_from_file(self, file_path):
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            self.populate_fields_from_config(data)
            QMessageBox.information(self, "Configuración cargada", f"Se cargó la configuración desde:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la configuración:\n{e}")

    def populate_fields_from_config(self, data):
        rpa = data.get("rpa", {})
        self.nombre_rpa.setText(rpa.get("nombre", ""))
        self.tipo_auth.setCurrentText(rpa.get("tipo_autenticacion", "form_js"))
        self.modo_visible.setChecked(rpa.get("modo_navegador_visible", False))

        # Usuario y password
        if rpa.get("tipo_autenticacion") == "form_js":
            self.auth_user.setText(rpa.get("form_js", {}).get("username_value", ""))
            self.auth_pass.setText(rpa.get("form_js", {}).get("password_value", ""))
        else:
            self.auth_user.setText(rpa.get("http_basic", {}).get("username", ""))
            self.auth_pass.setText(rpa.get("http_basic", {}).get("password", ""))

        # URLs y tiempos de espera
        # Borra los widgets de URLs existentes
        for widget in self.url_routes[:]:
            self.remove_url_widget(widget)
        # Agrega según el archivo (siempre al menos uno)
        url_ruta = rpa.get("url_ruta", [])
        for idx, ruta in enumerate(url_ruta):
            self.add_url_widget(is_initial=(idx == 0))
            self.url_routes[-1].url_input.setText(ruta.get("url", ""))
            self.url_routes[-1].wait_time_input.setValue(int(ruta.get("wait_time_ms", 10000)))
        if not url_ruta:  # Si no hay URLs, agrega uno vacío
            self.add_url_widget(is_initial=True)

        # --- Configuración de correo ---
        correo = data.get("correo", {})
        self.smtp_selector.setCurrentText("Remoto" if correo.get("usar_remoto") else "Local")
        self.remitente.setText(correo.get("remitente", ""))
        self.destinatarios.setText(", ".join(correo.get("destinatarios", [])))
        self.cc.setText(", ".join(correo.get("cc", [])))
        self.asunto.setText(correo.get("asunto", ""))
        self.incluir_fecha.setChecked(correo.get("incluir_fecha", False))
        self.cuerpo_html.setPlainText(correo.get("cuerpo_html", ""))

        # SMTP
        self.smtp_local.setText(
            f'{correo.get("smtp_local", {}).get("servidor", "")}:{correo.get("smtp_local", {}).get("puerto", "")}'
        )
        self.smtp_remoto.setText(
            f'{correo.get("smtp_remoto", {}).get("servidor", "")}:{correo.get("smtp_remoto", {}).get("puerto", "")}'
        )
        self.cred_remoto.setText(correo.get("smtp_remoto", {}).get("clave_aplicacion", ""))

        # --- Programación ---
        programacion = data.get("programacion", {})
        self.frecuencia.setCurrentText(programacion.get("frecuencia", "hourly"))
        self.intervalo.setText(str(programacion.get("intervalo", 6)))
        self.hora_inicio.setText(programacion.get("hora_inicio", "00:00"))

    def process_finished(self, exitCode, exitStatus):
        if exitCode == 0:
            QMessageBox.information(self, "Ejecución exitosa", "El RPA se ejecutó correctamente.")
        else:
            QMessageBox.warning(self, "Finalizado con errores", f"El RPA terminó con código: {exitCode}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ventana = RPAConfigUI()
    ventana.show()
    sys.exit(app.exec_())