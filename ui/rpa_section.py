from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QVBoxLayout, QPushButton, QLabel,
    QSizePolicy, QSpinBox, QHBoxLayout, QStackedWidget, QWidget
)
from widgets.url_route_widget import URLRouteWidget

def crear_seccion_rpa(parent):
    grupo = QGroupBox("Configuración RPA")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    # === Nombre del RPA ===
    parent.nombre_rpa = QLineEdit()
    parent.nombre_rpa.setPlaceholderText("Ej: Monitoreo Principal")
    parent.nombre_rpa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # === Tipo de autenticación ===
    parent.tipo_auth = QComboBox()
    parent.tipo_auth.addItems(["form_js", "http_basic"])
    parent.tipo_auth.currentTextChanged.connect(lambda tipo: update_auth_fields(parent, tipo))

    parent.modo_visible = QCheckBox("Modo navegador visible")

    form.addRow("Nombre del RPA:", parent.nombre_rpa)
    form.addRow("Tipo de autenticación:", parent.tipo_auth)
    form.addRow(parent.modo_visible)

    # === Autenticación form_js ===
    formjs_widget = QWidget()
    formjs_layout = QFormLayout(formjs_widget)

    parent.selector_user = QLineEdit()
    parent.selector_user.setPlaceholderText("#selector del input de usuario")

    parent.valor_user = QLineEdit()
    parent.valor_user.setPlaceholderText("Valor del usuario (Ej: admin)")

    parent.selector_pass = QLineEdit()
    parent.selector_pass.setPlaceholderText("#selector del input de contraseña")

    parent.valor_pass = QLineEdit()
    parent.valor_pass.setEchoMode(QLineEdit.Password)
    parent.valor_pass.setPlaceholderText("Valor de la contraseña")

    formjs_layout.addRow("Selector usuario:", parent.selector_user)
    formjs_layout.addRow("Valor usuario:", parent.valor_user)
    formjs_layout.addRow("Selector contraseña:", parent.selector_pass)
    formjs_layout.addRow("Valor contraseña:", parent.valor_pass)

    # === Autenticación http_basic ===
    basic_widget = QWidget()
    basic_layout = QFormLayout(basic_widget)

    parent.basic_user = QLineEdit()
    parent.basic_user.setPlaceholderText("Usuario (http_basic)")

    parent.basic_pass = QLineEdit()
    parent.basic_pass.setEchoMode(QLineEdit.Password)
    parent.basic_pass.setPlaceholderText("Contraseña (http_basic)")

    basic_layout.addRow("Usuario:", parent.basic_user)
    basic_layout.addRow("Contraseña:", parent.basic_pass)

    # === Stack dinámico de autenticación ===
    parent.auth_stacked = QStackedWidget()
    parent.auth_stacked.addWidget(formjs_widget)   # index 0
    parent.auth_stacked.addWidget(basic_widget)    # index 1

    form.addRow(parent.auth_stacked)

    # === Resolución del navegador ===
    parent.viewport_width = QSpinBox()
    parent.viewport_width.setRange(800, 3840)
    parent.viewport_width.setValue(1920)

    parent.viewport_height = QSpinBox()
    parent.viewport_height.setRange(600, 2160)
    parent.viewport_height.setValue(1080)

    pantalla_layout = QHBoxLayout()
    pantalla_layout.addWidget(QLabel("Ancho:"))
    pantalla_layout.addWidget(parent.viewport_width)
    pantalla_layout.addWidget(QLabel("Alto:"))
    pantalla_layout.addWidget(parent.viewport_height)

    parent.captura_completa = QCheckBox("Captura pantalla completa")
    parent.captura_completa.setChecked(True)

    form.addRow("Resolución navegador:", pantalla_layout)
    form.addRow(parent.captura_completa)

    # === Secuencia de URLs ===
    parent.urls_group = QGroupBox("Secuencia de URLs a visitar")
    parent.urls_layout = QVBoxLayout()
    parent.urls_list = QVBoxLayout()
    parent.url_routes = []

    parent.urls_layout.addLayout(parent.urls_list)

    parent.add_url_btn = QPushButton("Añadir URL")
    parent.add_url_btn.clicked.connect(lambda: add_url_widget(parent))
    parent.urls_layout.addWidget(parent.add_url_btn)

    parent.urls_group.setLayout(parent.urls_layout)
    form.addRow(parent.urls_group)

    grupo.setLayout(form)

    # Inicializaciones finales
    add_url_widget(parent, is_initial=True)
    update_auth_fields(parent, parent.tipo_auth.currentText())

    return grupo

def update_auth_fields(parent, auth_type):
    """Actualiza la vista del stack según el tipo de autenticación."""
    index = 0 if auth_type == "form_js" else 1
    parent.auth_stacked.setCurrentIndex(index)

def add_url_widget(parent, is_initial=False):
    """Añade un widget de URL con botón eliminar (excepto el primero)."""
    url_widget = URLRouteWidget(
        url_text="",
        wait_time=0 if is_initial else 10000
    )
    if not is_initial:
        url_widget.delete_btn.clicked.connect(lambda _, w=url_widget: remove_url_widget(parent, w))
    else:
        url_widget.delete_btn.setDisabled(True)

    parent.urls_list.addWidget(url_widget)
    parent.url_routes.append(url_widget)

def remove_url_widget(parent, widget):
    """Elimina un widget de URL de la interfaz."""
    parent.urls_list.removeWidget(widget)
    widget.setParent(None)
    parent.url_routes.remove(widget)