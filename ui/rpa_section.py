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

    # === Nombre y tipo de autenticación ===
    parent.nombre_rpa = QLineEdit()
    parent.nombre_rpa.setPlaceholderText("Ej: Monitoreo Principal")
    parent.nombre_rpa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    parent.tipo_auth = QComboBox()
    parent.tipo_auth.addItems(["form_js", "http_basic"])
    parent.tipo_auth.currentTextChanged.connect(lambda tipo: update_auth_fields(parent, tipo))

    form.addRow("Nombre del RPA:", parent.nombre_rpa)
    form.addRow("Tipo de autenticación:", parent.tipo_auth)

    # === Widgets para form_js ===
    formjs_widget = QWidget()
    formjs_layout = QFormLayout(formjs_widget)

    parent.valor_user = QLineEdit()
    parent.valor_pass = QLineEdit()
    parent.valor_pass.setEchoMode(QLineEdit.Password)

    formjs_layout.addRow("Usuario:", parent.valor_user)
    formjs_layout.addRow("Contraseña:", parent.valor_pass)

    # === Checkbox para selectores personalizados ===
    parent.checkbox_selectores = QCheckBox("Editar selectores")
    parent.checkbox_selectores.setChecked(True)
    parent.checkbox_selectores.stateChanged.connect(
        lambda state: parent.selectores_widget.setVisible(state == 2)
    )
    formjs_layout.addRow(parent.checkbox_selectores)

    parent.selectores_widget = QWidget()
    selectores_layout = QFormLayout(parent.selectores_widget)

    parent.selector_user = QLineEdit()
    parent.selector_user.setPlaceholderText("Ej: #user")
    parent.selector_pass = QLineEdit()
    parent.selector_pass.setPlaceholderText("Ej: #pass")

    selectores_layout.addRow("Selector usuario:", parent.selector_user)
    selectores_layout.addRow("Selector contraseña:", parent.selector_pass)

    formjs_layout.addRow(parent.selectores_widget)

    # === Widgets para http_basic ===
    basic_widget = QWidget()
    basic_layout = QFormLayout(basic_widget)

    parent.basic_user = QLineEdit()
    parent.basic_pass = QLineEdit()
    parent.basic_pass.setEchoMode(QLineEdit.Password)
    basic_layout.addRow("Usuario:", parent.basic_user)
    basic_layout.addRow("Contraseña:", parent.basic_pass)

    # === Stack dinámico de autenticación ===
    parent.auth_stacked = QStackedWidget()
    parent.auth_stacked.addWidget(formjs_widget)   # index 0
    parent.auth_stacked.addWidget(basic_widget)    # index 1
    form.addRow(parent.auth_stacked)

    # === Configuración de navegador ===
    navegador_group = QGroupBox("Configuración de Navegador")
    navegador_layout = QFormLayout()

    parent.modo_visible = QCheckBox("Modo navegador visible")

    parent.viewport_width = QSpinBox()
    parent.viewport_width.setRange(800, 3840)
    parent.viewport_width.setValue(1920)

    parent.viewport_height = QSpinBox()
    parent.viewport_height.setRange(600, 2160)
    parent.viewport_height.setValue(1080)

    resolucion_layout = QHBoxLayout()
    resolucion_layout.addWidget(QLabel("Ancho:"))
    resolucion_layout.addWidget(parent.viewport_width)
    resolucion_layout.addWidget(QLabel("Alto:"))
    resolucion_layout.addWidget(parent.viewport_height)

    parent.captura_completa = QCheckBox("Captura pantalla completa")
    parent.captura_completa.setChecked(True)

    navegador_layout.addRow(parent.modo_visible)
    navegador_layout.addRow("Resolución navegador:", resolucion_layout)
    navegador_layout.addRow(parent.captura_completa)
    navegador_group.setLayout(navegador_layout)

    form.addRow(navegador_group)

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

    # Inicialización
    add_url_widget(parent, is_initial=True)
    update_auth_fields(parent, parent.tipo_auth.currentText())

    return grupo

def update_auth_fields(parent, auth_type):
    """Actualiza el stack de autenticación."""
    index = 0 if auth_type == "form_js" else 1
    parent.auth_stacked.setCurrentIndex(index)

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