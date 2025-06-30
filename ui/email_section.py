from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QStackedWidget, QWidget,
    QLineEdit, QCheckBox, QTextEdit, QSizePolicy
)
from constants import PLANTILLA_HTML_POR_DEFECTO

def crear_seccion_email(parent):
    grupo = QGroupBox("Configuración de Correo")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    parent.smtp_selector = QComboBox()
    parent.smtp_selector.addItems(["Local", "Remoto"])
    parent.smtp_selector.currentTextChanged.connect(parent.update_smtp_fields)  # Esta función debe estar en main_window.py
    form.addRow("Proveedor SMTP:", parent.smtp_selector)

    parent.smtp_stack = QStackedWidget()

    # SMTP Local
    parent.smtp_local_widget = QWidget()
    local_layout = QFormLayout()
    parent.smtp_local = QLineEdit()
    parent.smtp_local.setPlaceholderText("servidor:puerto")
    parent.smtp_local.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    local_layout.addRow("Servidor SMTP:", parent.smtp_local)
    parent.smtp_local_widget.setLayout(local_layout)

    # SMTP Remoto
    parent.smtp_remoto_widget = QWidget()
    remoto_layout = QFormLayout()
    parent.smtp_remoto = QLineEdit()
    parent.cred_remoto = QLineEdit()
    parent.cred_remoto.setEchoMode(QLineEdit.Password)
    parent.smtp_remoto.setPlaceholderText("smtp.server.com:puerto")
    parent.cred_remoto.setPlaceholderText("Clave de aplicación")
    parent.smtp_remoto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    parent.cred_remoto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    remoto_layout.addRow("Servidor SMTP:", parent.smtp_remoto)
    remoto_layout.addRow("Clave Remota:", parent.cred_remoto)
    parent.smtp_remoto_widget.setLayout(remoto_layout)

    parent.smtp_stack.addWidget(parent.smtp_local_widget)
    parent.smtp_stack.addWidget(parent.smtp_remoto_widget)
    form.addRow(parent.smtp_stack)

    # Campos generales del correo
    parent.remitente = QLineEdit()
    parent.remitente.setPlaceholderText("example@dominio.com")
    parent.destinatarios = QLineEdit()
    parent.destinatarios.setPlaceholderText("correo1@dominio.com, correo2@dominio.com")
    parent.cc = QLineEdit()
    parent.cc.setPlaceholderText("correoCC@dominio.com")
    parent.asunto = QLineEdit()
    parent.incluir_fecha = QCheckBox("Incluir fecha en asunto")

    parent.cuerpo_html = QTextEdit()
    parent.cuerpo_html.setPlainText(PLANTILLA_HTML_POR_DEFECTO)
    parent.cuerpo_html.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    form.addRow("Remitente:", parent.remitente)
    form.addRow("Destinatarios:", parent.destinatarios)
    form.addRow("CC:", parent.cc)
    form.addRow("Asunto:", parent.asunto)
    form.addRow(parent.incluir_fecha)
    form.addRow("Cuerpo HTML:", parent.cuerpo_html)

    grupo.setLayout(form)
    return grupo