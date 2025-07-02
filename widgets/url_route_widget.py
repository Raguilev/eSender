from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QSizePolicy, QCheckBox
)

class URLRouteWidget(QWidget):
    def __init__(self, url_text='', wait_time=10000, capturar=True, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://servidor.com/ruta")
        self.url_input.setText(url_text)
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.url_input.setToolTip("Ingrese la URL que debe visitar el RPA")

        self.wait_time_input = QSpinBox()
        self.wait_time_input.setRange(1000, 300000)
        self.wait_time_input.setSingleStep(1000)
        self.wait_time_input.setValue(wait_time)
        self.wait_time_input.setSuffix(" ms")
        self.wait_time_input.setToolTip("Tiempo de espera antes de continuar (en milisegundos)")

        self.capture_checkbox = QCheckBox("Capturar")
        self.capture_checkbox.setChecked(capturar)
        self.capture_checkbox.setToolTip("Marcar si desea capturar pantalla al visitar esta URL")

        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.setToolTip("Eliminar esta URL de la secuencia")

        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input)
        layout.addWidget(QLabel("Espera:"))
        layout.addWidget(self.wait_time_input)
        layout.addWidget(self.capture_checkbox)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    def get_data(self):
        return {
            "url": self.url_input.text().strip(),
            "wait_time_ms": self.wait_time_input.value(),
            "capturar": self.capture_checkbox.isChecked()
        }