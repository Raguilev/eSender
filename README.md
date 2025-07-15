
# eSender - Sistema de Despliegue Seguro de RPA

Este proyecto permite crear, cifrar, desplegar y ejecutar automatizaciones (RPA) de forma segura, incorporando navegación con Playwright, envío automático de correos y programación de tareas. Está diseñado para proteger la confidencialidad de la configuración, incluso en entornos donde se distribuyen los RPAs como ejecutables o scripts autónomos.

---

## Características Principales

### Seguridad
- Cifrado de la configuración en formato `.enc` usando **AES-256-CBC**.
- Separación de la clave simétrica (`.key`) respecto al contenido cifrado.
- Ejecución autónoma sin necesidad de exponer el contenido del JSON original.
- Control total del entorno de ejecución a través del script `run_rpa.py`.

### Interfaz de Usuario (UI)
- Construida en **PyQt5**, permite al usuario crear y editar configuraciones RPA:
  - Modo visible o headless.
  - Lista de URLs con tiempos de espera y autenticación opcional.
  - Captura de pantalla automatizada.
  - Configuración SMTP (servidor local o Gmail).
  - Programación de tareas recurrentes.

### Compatibilidad multiplataforma
- Generación de scripts `.bat` (Windows) o `.sh` (macOS/Linux) para tareas programadas.
- Validación de parámetros en tiempo real.
- Uso de `run_rpa.py` con interfaz CLI compatible con cualquier OS que tenga Python 3+.

---

## Flujo del Sistema

El flujo completo del sistema comprende las siguientes etapas:

### 1. Creación y Configuración
- El usuario edita los campos necesarios desde la UI: nombre, URLs, correos, horario, etc.
- Puede cargar una configuración existente o comenzar una nueva.

### 2. Cifrado y Despliegue
- Al presionar `Deploy`, se genera un paquete cifrado que incluye:
  - `rpa_config.enc`: configuración cifrada.
  - `rpa.key`: clave secreta de cifrado.
  - `run_rpa.py`: script autónomo que ejecuta el RPA.
  - Carpeta `rpa_runner/`: motor de ejecución con navegación y envío de correo.
  - Script de programación automática (`.bat` o `.sh`).
  - Instrucciones detalladas.

### 3. Ejecución
- El paquete puede ejecutarse con:
  ```bash
  python run_rpa.py rpa_config.enc rpa.key
  ```
- El script desencripta el archivo `.enc`, realiza las capturas, guarda los resultados y envía un correo automático.

### 4. Programación
- El script generado permite automatizar la ejecución diaria, semanal o en intervalos definidos por el usuario.
- Compatible con `crontab` en Unix/macOS y `SCHTASKS` en Windows.

### 5. Validación y Seguridad
- Si alguien intenta modificar `decryptor.py` para revelar el JSON, debe tener:
  - La clave `.key`
  - El archivo `.enc`
  - Conocimiento del mecanismo de padding y AES-CBC
- El contenido no es visible sin desencriptarlo correctamente.

---

## Estructura del Proyecto

```
eSender_rpa/
│
├── ui/
│   ├── main_window.py
│   ├── rpa_section.py
│   ├── email_section.py
│   ├── schedule_section.py
│   ├── buttons_section.py
│   ├── buttons_section.py
│   ├── url_route_widget.py
│   └── config_loader.py
│
├── deploy_handler/
│   ├── deploy_handler.py
│   ├── encryptor.py
│   ├── decryptor.py
│   └── run_rpa_enc.py
│
├── rpa_runner/
│   ├── navigation.py
│   └── mailer.py
│
├── constants/
│   └── constants.py
│
├── schemas/
│   └── rpa_email.schema.json
│
├── main.py
├── run_rpa.py
└── requirements.txt
```

---

## Ejemplo de Uso

```bash
# Ejecutar paquete seguro
python run_rpa.py rpa_config.enc rpa.key

# Desencriptar (para debugging)
python decryptor.py rpa_config.enc rpa.key
```

---

## Requisitos

- Python 3.8 o superior
- Playwright (con navegadores instalados)
- PyQt5
- pycryptodome
- requests, tqdm, email (built-in)

Instalación recomendada:
```bash
pip install -r requirements.txt
playwright install
```

---

## Consideraciones Finales

- La ejecución no expone el contenido sensible en ningún momento.
- El sistema puede utilizarse para múltiples RPAs configurados con distintos tiempos, frecuencias y destinos.
- Se recomienda usar claves distintas por RPA para mayor seguridad.

---

## Licencia

Este sistema puede ser reutilizado o extendido bajo los principios de seguridad de la información, evitando exponer la configuración sensible en entornos no confiables.
