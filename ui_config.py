import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout,
    QMessageBox, QGroupBox, QFormLayout, QComboBox, QStackedWidget
)
from deploy_handler import create_rpa_package
from jsonschema import validate, ValidationError
from PyQt5.QtCore import QProcess

class RPAConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de configuración RPA")
        self.setGeometry(100, 100, 800, 700)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.config = {
            "rpa": {},
            "correo": {},
            "programacion": {}
        }

        self.file_path = "rpa_email.json"
        self.init_ui()

    def init_ui(self):
        self.rpa_group = QGroupBox("Configuración RPA")
        self.rpa_form = QFormLayout()

        self.nombre_rpa = QLineEdit()
        self.tipo_auth = QComboBox()
        self.tipo_auth.addItems(["form_js", "http_basic"])
        self.tipo_auth.currentTextChanged.connect(self.update_auth_fields)

        self.url_acceso = QLineEdit()
        self.url_dashboard = QLineEdit()
        self.modo_visible = QCheckBox("Modo navegador Visible")

        self.rpa_form.addRow("Nombre RPA:", self.nombre_rpa)
        self.rpa_form.addRow("Tipo de autenticación:", self.tipo_auth)
        self.rpa_form.addRow("URL de acceso:", self.url_acceso)
        self.rpa_form.addRow("URL de dashboard:", self.url_dashboard)
        self.rpa_form.addRow(self.modo_visible)

        self.auth_user = QLineEdit()
        self.auth_pass = QLineEdit()
        self.auth_pass.setEchoMode(QLineEdit.Password)
        self.auth_user.setPlaceholderText("Usuario")
        self.auth_pass.setPlaceholderText("Contraseña")
        self.rpa_form.addRow("Usuario:", self.auth_user)
        self.rpa_form.addRow("Contraseña:", self.auth_pass)

        self.rpa_group.setLayout(self.rpa_form)

        self.correo_group = QGroupBox("Configuración de Correo")
        self.correo_form = QFormLayout()

        self.smtp_selector = QComboBox()
        self.smtp_selector.addItems(["Local", "Remoto"])
        self.smtp_selector.currentTextChanged.connect(self.update_smtp_fields)
        self.correo_form.addRow("Proveedor SMTP:", self.smtp_selector)

        self.smtp_stack = QStackedWidget()

        self.smtp_local_widget = QWidget()
        local_layout = QFormLayout()
        self.smtp_local = QLineEdit()
        self.smtp_local.setPlaceholderText("server:port")
        local_layout.addRow("Servidor SMTP:", self.smtp_local)
        self.smtp_local_widget.setLayout(local_layout)

        self.smtp_remoto_widget = QWidget()
        remoto_layout = QFormLayout()
        self.smtp_remoto = QLineEdit()
        self.cred_remoto = QLineEdit()
        self.cred_remoto.setEchoMode(QLineEdit.Password)
        self.smtp_remoto.setPlaceholderText("smtp.server.com:port")
        self.cred_remoto.setPlaceholderText("Clave de aplicación")
        remoto_layout.addRow("Servidor SMTP:", self.smtp_remoto)
        remoto_layout.addRow("Clave Remota:", self.cred_remoto)
        self.smtp_remoto_widget.setLayout(remoto_layout)

        self.smtp_stack.addWidget(self.smtp_local_widget)
        self.smtp_stack.addWidget(self.smtp_remoto_widget)
        self.correo_form.addRow(self.smtp_stack)

        self.remitente = QLineEdit()
        self.destinatarios = QLineEdit()
        self.cc = QLineEdit()
        self.asunto = QLineEdit()
        self.incluir_fecha = QCheckBox("Incluir fecha en asunto")
        self.cuerpo_html = QTextEdit()

        self.correo_form.addRow("Remitente:", self.remitente)
        self.correo_form.addRow("Destinatarios:", self.destinatarios)
        self.correo_form.addRow("CC:", self.cc)
        self.correo_form.addRow("Asunto:", self.asunto)
        self.correo_form.addRow(self.incluir_fecha)
        self.correo_form.addRow("Cuerpo HTML:", self.cuerpo_html)
        self.correo_group.setLayout(self.correo_form)

        self.schedule_group = QGroupBox("Programación de tarea automatizada")
        self.schedule_form = QFormLayout()

        self.frecuencia = QComboBox()
        self.frecuencia.addItems(["hourly", "daily", "weekly"])
        self.intervalo = QLineEdit("6")
        self.hora_inicio = QLineEdit("00:00")

        self.schedule_form.addRow("Frecuencia:", self.frecuencia)
        self.schedule_form.addRow("Intervalo (ej. cada X horas/días):", self.intervalo)
        self.schedule_form.addRow("Hora de inicio (HH:MM):", self.hora_inicio)
        self.schedule_group.setLayout(self.schedule_form)

        self.save_button = QPushButton("Guardar JSON")
        self.save_button.clicked.connect(self.save_config)

        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.run_test_rpa)

        self.deploy_button = QPushButton("Deploy")
        self.deploy_button.clicked.connect(self.deploy_rpa)

        self.layout.addWidget(self.rpa_group)
        self.layout.addWidget(self.correo_group)
        self.layout.addWidget(self.schedule_group)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.deploy_button)
        self.layout.addLayout(button_layout)

        self.update_auth_fields(self.tipo_auth.currentText())
        self.update_smtp_fields()

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

            self.config["rpa"] = {
                "nombre": self.nombre_rpa.text(),
                "modo_navegador_visible": self.modo_visible.isChecked(),
                "tipo_autenticacion": self.tipo_auth.currentText(),
                "url_acceso": self.url_acceso.text(),
                "url_dashboard": self.url_dashboard.text(),
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
                "destinatarios": [x.strip() for x in self.destinatarios.text().split(",")],
                "cc": [x.strip() for x in self.cc.text().split(",")],
                "asunto": self.asunto.text(),
                "incluir_fecha": self.incluir_fecha.isChecked(),
                "cuerpo_html": self.cuerpo_html.toPlainText()
            }

            self.config["programacion"] = {
                "frecuencia": self.frecuencia.currentText(),
                "intervalo": int(self.intervalo.text()),
                "hora_inicio": self.hora_inicio.text()
            }

            with open("rpa_email.schema.json", encoding="utf-8") as schema_file:
                schema = json.load(schema_file)
                validate(instance=self.config, schema=schema)

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
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
