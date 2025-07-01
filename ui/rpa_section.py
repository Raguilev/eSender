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

    # === Nombre del RPA y autenticación ===
    parent.nombre_rpa = QLineEdit()
    parent.nombre_rpa.setPlaceholderText("Ej: Monitoreo Principal")

    parent.tipo_auth = QComboBox()
    parent.tipo_auth.addItems(["form_js", "http_basic"])
    parent.tipo_auth.currentTextChanged.connect(lambda tipo: update_auth_fields(parent, tipo))

    form.addRow("Nombre del RPA:", parent.nombre_rpa)
    form.addRow("Tipo de autenticación:", parent.tipo_auth)

    # === Autenticación form_js ===
    formjs_widget = QWidget()
    formjs_layout = QFormLayout(formjs_widget)

    # Selectores ocultables
    parent.selector_user = QLineEdit()
    parent.selector_user.setPlaceholderText("#selector del input de usuario")

    parent.selector_pass = QLineEdit()
    parent.selector_pass.setPlaceholderText("#selector del input de contraseña")

    # Valores visibles siempre
    parent.valor_user = QLineEdit()
    parent.valor_user.setPlaceholderText("Valor del usuario (Ej: admin)")

    parent.valor_pass = QLineEdit()
    parent.valor_pass.setEchoMode(QLineEdit.Password)
    parent.valor_pass.setPlaceholderText("Valor de la contraseña")

    # Grupo para selectores opcionales (ocultables)
    parent.selectores_widget = QWidget()
    selectores_layout = QFormLayout(parent.selectores_widget)
    selectores_layout.addRow("Selector usuario:", parent.selector_user)
    selectores_layout.addRow("Selector contraseña:", parent.selector_pass)

    # Checkbox para mostrar/ocultar selectores
    parent.toggle_selectores = QCheckBox("Selectores personalizados")
    parent.toggle_selectores.setChecked(False)
    parent.toggle_selectores.toggled.connect(lambda state: parent.selectores_widget.setVisible(state))

    # Layout final del form_js
    formjs_layout.addRow(parent.toggle_selectores)
    formjs_layout.addRow(parent.selectores_widget)
    formjs_layout.addRow("Valor usuario:", parent.valor_user)
    formjs_layout.addRow("Valor contraseña:", parent.valor_pass)

    parent.selectores_widget.setVisible(False)  # Ocultar por defecto

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

    # === Stack de autenticación ===
    parent.auth_stacked = QStackedWidget()
    parent.auth_stacked.addWidget(formjs_widget)   # index 0
    parent.auth_stacked.addWidget(basic_widget)    # index 1
    form.addRow(parent.auth_stacked)

    # === Configuración navegador ===
    navegador_group = QGroupBox("Configuración de Navegador")
    navegador_layout = QFormLayout()

    parent.viewport_width = QSpinBox()
    parent.viewport_width.setRange(800, 3840)
    parent.viewport_width.setValue(1920)

    parent.viewport_height = QSpinBox()
    parent.viewport_height.setRange(600, 2160)
    parent.viewport_height.setValue(1080)

    resol_layout = QHBoxLayout()
    resol_layout.addWidget(QLabel("Ancho:"))
    resol_layout.addWidget(parent.viewport_width)
    resol_layout.addWidget(QLabel("Alto:"))
    resol_layout.addWidget(parent.viewport_height)

    parent.captura_completa = QCheckBox("Captura pantalla completa")
    parent.captura_completa.setChecked(True)

    parent.modo_visible = QCheckBox("Modo navegador visible")

    navegador_layout.addRow("Resolución navegador:", resol_layout)
    navegador_layout.addRow(parent.captura_completa)
    navegador_layout.addRow(parent.modo_visible)
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

    # Inicializaciones finales
    add_url_widget(parent, is_initial=True)
    update_auth_fields(parent, parent.tipo_auth.currentText())

    return grupo

def update_auth_fields(parent, auth_type):
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