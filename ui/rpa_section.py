from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy, QSpinBox,
    QHBoxLayout, QCheckBox, QWidget
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
    form.addRow("Nombre del RPA:", parent.nombre_rpa)

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

    # === Secuencia de URLs con configuración individual ===
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