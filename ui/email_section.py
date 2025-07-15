from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QStackedWidget, QWidget,
    QLineEdit, QCheckBox, QTextEdit, QSizePolicy, QHBoxLayout,
    QLabel, QPushButton, QMessageBox
)
import smtplib
from constants.constants import PLANTILLA_HTML_POR_DEFECTO

def crear_seccion_email(parent):
    grupo = QGroupBox("Configuración de Correo")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    # === Selector de proveedor SMTP ===
    parent.smtp_selector = QComboBox()
    parent.smtp_selector.addItems(["Local", "Remoto"])
    parent.smtp_selector.setToolTip("Seleccione el tipo de servidor SMTP que desea utilizar")
    form.addRow("Proveedor SMTP:", parent.smtp_selector)

    parent.smtp_stack = QStackedWidget()

    # =========== SMTP LOCAL ==========
    parent.smtp_local_widget = QWidget()
    local_layout = QFormLayout()

    parent.smtp_local_host = QLineEdit()
    parent.smtp_local_host.setPlaceholderText("Ej: 10.66.250.230")
    parent.smtp_local_host.setToolTip("Dirección IP o dominio del servidor SMTP local")

    parent.smtp_local_port = QLineEdit()
    parent.smtp_local_port.setFixedWidth(80)
    parent.smtp_local_port.setPlaceholderText("Ej: 25")
    parent.smtp_local_port.setToolTip("Puerto del servidor SMTP local (Ej: 25, 587)")

    local_row = QHBoxLayout()
    local_row.addWidget(QLabel("Host:"))
    local_row.addWidget(parent.smtp_local_host)
    local_row.addWidget(QLabel("Puerto:"))
    local_row.addWidget(parent.smtp_local_port)

    local_layout.addRow(local_row)
    parent.smtp_local_widget.setLayout(local_layout)

    # =========== SMTP REMOTO ==========
    parent.smtp_remoto_widget = QWidget()
    remoto_layout = QFormLayout()

    parent.smtp_remoto_host = QLineEdit()
    parent.smtp_remoto_host.setPlaceholderText("Ej: smtp.gmail.com")
    parent.smtp_remoto_host.setToolTip("Servidor SMTP remoto, como smtp.gmail.com")

    parent.smtp_remoto_port = QLineEdit()
    parent.smtp_remoto_port.setFixedWidth(80)
    parent.smtp_remoto_port.setPlaceholderText("Ej: 587")
    parent.smtp_remoto_port.setToolTip("Puerto SMTP para conexión segura (usualmente 587)")

    parent.smtp_remoto_user = QLineEdit()
    parent.smtp_remoto_user.setPlaceholderText("Ej: example@gmail.com")
    parent.smtp_remoto_user.setToolTip("Correo electrónico usado como remitente")

    parent.cred_remoto = QLineEdit()
    parent.cred_remoto.setEchoMode(QLineEdit.Password)
    parent.cred_remoto.setPlaceholderText("Clave de aplicación de Gmail")
    parent.cred_remoto.setToolTip("Clave generada desde la cuenta de Google para aplicaciones")

    remoto_row = QHBoxLayout()
    remoto_row.addWidget(QLabel("Host:"))
    remoto_row.addWidget(parent.smtp_remoto_host)
    remoto_row.addWidget(QLabel("Puerto:"))
    remoto_row.addWidget(parent.smtp_remoto_port)

    remoto_layout.addRow(remoto_row)
    remoto_layout.addRow("Usuario (correo):", parent.smtp_remoto_user)
    remoto_layout.addRow("Clave de aplicación:", parent.cred_remoto)

    parent.smtp_remoto_widget.setLayout(remoto_layout)

    # Añadir widgets al stack
    parent.smtp_stack.addWidget(parent.smtp_local_widget)
    parent.smtp_stack.addWidget(parent.smtp_remoto_widget)
    parent.smtp_stack.setCurrentWidget(parent.smtp_local_widget)

    form.addRow(parent.smtp_stack)

    # =========== Datos generales del correo ==========
    parent.remitente = QLineEdit()
    parent.remitente.setPlaceholderText("Ej: example@dominio.com")
    parent.remitente.setToolTip("Correo desde el cual se enviará el reporte")

    parent.destinatarios = QLineEdit()
    parent.destinatarios.setPlaceholderText("correo1@dominio.com, correo2@dominio.com")
    parent.destinatarios.setToolTip("Lista de correos destino separados por coma")

    parent.cc = QLineEdit()
    parent.cc.setPlaceholderText("correoCC@dominio.com")
    parent.cc.setToolTip("Correos en copia (opcional)")

    parent.asunto = QLineEdit()
    parent.asunto.setPlaceholderText("Ej: Reporte automático de monitoreo")
    parent.asunto.setToolTip("Asunto del correo electrónico")

    parent.incluir_fecha = QCheckBox("Incluir fecha en asunto")
    parent.incluir_fecha.setToolTip("Agrega la fecha actual al final del asunto")

    parent.cuerpo_html = QTextEdit()
    parent.cuerpo_html.setPlainText(PLANTILLA_HTML_POR_DEFECTO)
    parent.cuerpo_html.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    parent.cuerpo_html.setToolTip("Cuerpo del mensaje en formato HTML")

    form.addRow("Remitente:", parent.remitente)
    form.addRow("Destinatarios:", parent.destinatarios)
    form.addRow("CC:", parent.cc)
    form.addRow("Asunto:", parent.asunto)
    form.addRow(parent.incluir_fecha)
    form.addRow("Cuerpo HTML:", parent.cuerpo_html)

    # =========== Adjuntar capturas ===========
    parent.adjuntar_capturas = QCheckBox("Adjuntar capturas como archivos PNG")
    parent.adjuntar_capturas.setChecked(False)
    parent.adjuntar_capturas.setToolTip("Adjunta cada captura como archivo en lugar de insertarlas en el HTML")
    form.addRow(parent.adjuntar_capturas)

    # =========== Botón: Probar Conexión ==========
    btn_test_smtp = QPushButton("Probar conexión SMTP")
    btn_test_smtp.clicked.connect(lambda: probar_conexion_smtp(parent))
    form.addRow(btn_test_smtp)

    grupo.setLayout(form)

    # === Sincronizar remitente con cuenta remota ===
    def sincronizar_remitente():
        if parent.smtp_selector.currentText() == "Remoto" and not parent.remitente.text().strip():
            parent.remitente.setText(parent.smtp_remoto_user.text())

    def al_cambiar_smtp(opcion):
        if opcion == "Remoto":
            sincronizar_remitente()

    parent.smtp_remoto_user.textChanged.connect(sincronizar_remitente)
    parent.smtp_selector.currentTextChanged.connect(al_cambiar_smtp)
    parent.smtp_selector.currentTextChanged.connect(parent.update_smtp_fields)

    return grupo

def probar_conexion_smtp(parent):
    try:
        if parent.smtp_selector.currentText() == "Local":
            servidor = parent.smtp_local_host.text().strip()
            puerto_texto = parent.smtp_local_port.text().strip()

            if not servidor or not puerto_texto:
                raise ValueError("Debe completar el host y puerto para conexión local.")

            if not puerto_texto.isdigit() or int(puerto_texto) <= 0:
                raise ValueError("El puerto debe ser un número entero positivo.")

            puerto = int(puerto_texto)
            with smtplib.SMTP(servidor, puerto, timeout=5) as server:
                code, msg = server.noop()
                if code != 250:
                    raise ConnectionError(f"Respuesta inesperada del servidor: {msg.decode()}")

        else:  # Remoto
            servidor = parent.smtp_remoto_host.text().strip()
            puerto_texto = parent.smtp_remoto_port.text().strip()
            usuario = parent.smtp_remoto_user.text().strip()
            clave = parent.cred_remoto.text().strip()

            if not servidor or not puerto_texto or not usuario or not clave:
                raise ValueError("Debe completar todos los campos para conexión remota.")

            if not puerto_texto.isdigit() or int(puerto_texto) <= 0:
                raise ValueError("El puerto debe ser un número entero positivo.")

            puerto = int(puerto_texto)
            with smtplib.SMTP(servidor, puerto, timeout=5) as server:
                server.starttls()
                server.login(usuario, clave)

        QMessageBox.information(parent, "Éxito", "Conexión SMTP exitosa.")

    except ValueError as ve:
        QMessageBox.warning(parent, "Campos incompletos", str(ve))
    except smtplib.SMTPAuthenticationError:
        QMessageBox.critical(parent, "Error de autenticación", "Usuario o clave incorrectos para SMTP remoto.")
    except smtplib.SMTPConnectError:
        QMessageBox.critical(parent, "Error de conexión", "No se pudo establecer conexión con el servidor SMTP.")
    except Exception as e:
        QMessageBox.critical(parent, "Fallo de conexión", f"No se pudo establecer conexión:\n{str(e)}")