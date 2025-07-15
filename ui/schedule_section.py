from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QLineEdit
)
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp

def crear_seccion_schedule(parent):
    grupo = QGroupBox("Programación de tarea automatizada")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    # === Frecuencia programada ===
    parent.frecuencia = QComboBox()
    parent.frecuencia.addItems(["hourly", "daily", "weekly"])
    parent.frecuencia.setToolTip("Periodicidad general con la que se ejecutará el RPA.")

    # === Intervalo ===
    parent.intervalo = QLineEdit()
    parent.intervalo.setValidator(QIntValidator(1, 999))
    parent.intervalo.setText("6")
    parent.intervalo.setPlaceholderText("Ej: 6")
    parent.intervalo.setToolTip("Intervalo de tiempo según la frecuencia seleccionada.")

    # === Hora de inicio ===
    parent.hora_inicio = QLineEdit()
    regex_hora = QRegExp("^(?:[01]\\d|2[0-3]):[0-5]\\d$")
    parent.hora_inicio.setValidator(QRegExpValidator(regex_hora))
    parent.hora_inicio.setText("00:00")
    parent.hora_inicio.setPlaceholderText("Ej: 08:30")
    parent.hora_inicio.setToolTip("Hora de inicio en formato 24h (HH:MM).")

    # === Sistema operativo de destino ===
    parent.sistema_destino = QComboBox()
    parent.sistema_destino.addItems(["windows", "linux"])
    parent.sistema_destino.setToolTip("Sistema donde se desplegará y ejecutará el RPA.")

    # === Agregar al formulario ===
    form.addRow("Frecuencia:", parent.frecuencia)
    form.addRow("Intervalo:", parent.intervalo)
    form.addRow("Hora de inicio:", parent.hora_inicio)
    form.addRow("Sistema operativo:", parent.sistema_destino)

    grupo.setLayout(form)
    return grupo