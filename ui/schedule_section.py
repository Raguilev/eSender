from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QLineEdit, QLabel
)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QTime

def crear_seccion_schedule(parent):
    grupo = QGroupBox("Programación de tarea automatizada")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    # === Frecuencia programada ===
    parent.frecuencia = QComboBox()
    parent.frecuencia.addItems([
        "hourly",   # cada X horas
        "daily",    # cada X días
        "weekly"    # cada X semanas
    ])
    parent.frecuencia.setToolTip("Periodicidad general del RPA")

    # === Intervalo ===
    parent.intervalo = QLineEdit("6")
    parent.intervalo.setValidator(QIntValidator(1, 999))
    parent.intervalo.setPlaceholderText("Número entero (Ej: 6)")
    parent.intervalo.setToolTip("Intervalo según frecuencia. Ej: cada 6 horas.")

    # === Hora de inicio ===
    parent.hora_inicio = QLineEdit("00:00")
    parent.hora_inicio.setPlaceholderText("HH:MM (formato 24h)")
    parent.hora_inicio.setToolTip("Hora en la que se inicia la ejecución programada.")

    form.addRow("Frecuencia:", parent.frecuencia)
    form.addRow("Intervalo:", parent.intervalo)
    form.addRow("Hora de inicio:", parent.hora_inicio)

    grupo.setLayout(form)
    return grupo