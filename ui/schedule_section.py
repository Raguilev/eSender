from PyQt5.QtWidgets import QGroupBox, QFormLayout, QComboBox, QLineEdit

def crear_seccion_schedule(parent):
    grupo = QGroupBox("Programación de tarea automatizada")
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

    parent.frecuencia = QComboBox()
    parent.frecuencia.addItems(["hourly", "daily", "weekly"])

    parent.intervalo = QLineEdit("6")
    parent.hora_inicio = QLineEdit("00:00")

    form.addRow("Frecuencia:", parent.frecuencia)
    form.addRow("Intervalo (ej. cada X horas/días):", parent.intervalo)
    form.addRow("Hora de inicio (HH:MM):", parent.hora_inicio)

    grupo.setLayout(form)
    return grupo