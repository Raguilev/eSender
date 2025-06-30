from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QVBoxLayout, QPushButton, QLabel,
    QSizePolicy, QSpinBox, QHBoxLayout
)
from widgets.url_route_widget import URLRouteWidget

def crear_seccion_rpa(parent):
    grupo = QGroupBox("Configuración RPA")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    # Campo: Nombre del RPA
    parent.nombre_rpa = QLineEdit()
    parent.nombre_rpa.setPlaceholderText("Ej: Monitoreo Principal")
    parent.nombre_rpa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Campo: Tipo de autenticación
    parent.tipo_auth = QComboBox()
    parent.tipo_auth.addItems(["form_js", "http_basic"])
    parent.tipo_auth.currentTextChanged.connect(lambda tipo: update_auth_fields(parent, tipo))

    parent.modo_visible = QCheckBox("Modo navegador visible")

    form.addRow("Nombre RPA:", parent.nombre_rpa)
    form.addRow("Tipo de autenticación:", parent.tipo_auth)
    form.addRow(parent.modo_visible)

    # Campos: Usuario y contraseña
    parent.auth_user = QLineEdit()
    parent.auth_pass = QLineEdit()
    parent.auth_pass.setEchoMode(QLineEdit.Password)
    parent.auth_user.setPlaceholderText("Usuario")
    parent.auth_pass.setPlaceholderText("Contraseña")
    form.addRow("Usuario:", parent.auth_user)
    form.addRow("Contraseña:", parent.auth_pass)

    # Campos: Pantalla
    parent.viewport_width = QSpinBox()
    parent.viewport_width.setRange(800, 3840)
    parent.viewport_width.setValue(1920)

    parent.viewport_height = QSpinBox()
    parent.viewport_height.setRange(600, 2160)
    parent.viewport_height.setValue(1080)

    parent.captura_completa = QCheckBox("Captura pantalla completa")
    parent.captura_completa.setChecked(True)

    pantalla_layout = QHBoxLayout()
    pantalla_layout.addWidget(QLabel("Ancho:"))
    pantalla_layout.addWidget(parent.viewport_width)
    pantalla_layout.addWidget(QLabel("Alto:"))
    pantalla_layout.addWidget(parent.viewport_height)

    form.addRow("Resolución navegador:", pantalla_layout)
    form.addRow(parent.captura_completa)

    # URLs dinámicas
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

    # Agregar primer URL obligatorio
    add_url_widget(parent, is_initial=True)

    # Inicializar placeholders de usuario/clave según tipo seleccionado
    update_auth_fields(parent, parent.tipo_auth.currentText())

    return grupo

def add_url_widget(parent, is_initial=False):
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
    parent.urls_list.removeWidget(widget)
    widget.setParent(None)
    parent.url_routes.remove(widget)

def update_auth_fields(parent, auth_type):
    if auth_type == "form_js":
        parent.auth_user.setPlaceholderText("Selector + valor usuario (form_js)")
        parent.auth_pass.setPlaceholderText("Selector + valor contraseña (form_js)")
    else:
        parent.auth_user.setPlaceholderText("Usuario (http_basic)")
        parent.auth_pass.setPlaceholderText("Contraseña (http_basic)")