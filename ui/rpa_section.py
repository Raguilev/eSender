from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy, QSpinBox,
    QHBoxLayout, QCheckBox, QWidget
)
from .url_route_widget import URLRouteWidget


def crear_seccion_rpa(parent):
    grupo = QGroupBox("Configuración del RPA")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    # === Nombre del RPA ===
    parent.nombre_rpa = QLineEdit()
    parent.nombre_rpa.setPlaceholderText("Ej: Monitoreo Principal")
    parent.nombre_rpa.setToolTip("Nombre identificador del flujo RPA.")
    parent.nombre_rpa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    form.addRow("Nombre del RPA:", parent.nombre_rpa)

    # === Configuración del navegador ===
    navegador_group = QGroupBox("Configuración del navegador")
    navegador_layout = QFormLayout()

    parent.modo_visible = QCheckBox("Mostrar navegador durante la ejecución")
    parent.modo_visible.setToolTip("Activa o desactiva el modo headless del navegador.")

    # Resolución personalizada
    parent.viewport_width = QSpinBox()
    parent.viewport_width.setRange(800, 3840)
    parent.viewport_width.setValue(1920)
    parent.viewport_width.setToolTip("Ancho del navegador en píxeles.")

    parent.viewport_height = QSpinBox()
    parent.viewport_height.setRange(600, 2160)
    parent.viewport_height.setValue(1080)
    parent.viewport_height.setToolTip("Alto del navegador en píxeles.")

    resolucion_layout = QHBoxLayout()
    resolucion_layout.addWidget(QLabel("Ancho:"))
    resolucion_layout.addWidget(parent.viewport_width)
    resolucion_layout.addWidget(QLabel("Alto:"))
    resolucion_layout.addWidget(parent.viewport_height)

    parent.captura_completa = QCheckBox("Capturar página completa")
    parent.captura_completa.setChecked(True)
    parent.captura_completa.setToolTip("Captura la página completa (scroll total) en lugar de solo la vista inicial.")

    navegador_layout.addRow(parent.modo_visible)
    navegador_layout.addRow("Resolución del navegador:", resolucion_layout)
    navegador_layout.addRow(parent.captura_completa)
    navegador_group.setLayout(navegador_layout)

    form.addRow(navegador_group)

    # === Secuencia de URLs con configuración dinámica ===
    parent.urls_group = QGroupBox("Secuencia de URLs")
    parent.urls_layout = QVBoxLayout()
    parent.urls_list = QVBoxLayout()
    parent.url_routes = []

    parent.urls_layout.addLayout(parent.urls_list)

    parent.add_url_btn = QPushButton("Añadir URL")
    parent.add_url_btn.setToolTip("Agrega una nueva URL al flujo RPA")
    parent.add_url_btn.clicked.connect(lambda: add_url_widget(parent))
    parent.urls_layout.addWidget(parent.add_url_btn)

    parent.urls_group.setLayout(parent.urls_layout)
    form.addRow(parent.urls_group)

    grupo.setLayout(form)

    # Agrega una URL inicial protegida contra eliminación
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
        url_widget.delete_btn.setToolTip("No puedes eliminar la primera URL.")

    parent.urls_list.addWidget(url_widget)
    parent.url_routes.append(url_widget)


def remove_url_widget(parent, widget):
    parent.urls_list.removeWidget(widget)
    widget.setParent(None)
    parent.url_routes.remove(widget)