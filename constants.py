# constants.py

# === Plantilla HTML por defecto para cuerpo de correo ===
PLANTILLA_HTML_POR_DEFECTO = """
<p>Estimado equipo,</p>

<p>Se ha generado correctamente el siguiente reporte automático desde la plataforma <b>{{nombre_rpa}}</b>.</p>

<p><b>Fecha y hora de captura:</b> {{fecha}}</p>

<p><b>Secuencia completa de URLs visitadas:</b></p>
{{lista_urls}}

<p><b>Capturas realizadas:</b></p>
<p>Las capturas correspondientes a las URLs seleccionadas se muestran a continuación en orden de ejecución.</p>

{{bloque_capturas}}

<br><p><small>Este mensaje fue generado automáticamente por el sistema RPA.</small></p>
"""

# === Rutas importantes del proyecto ===
RUTA_CONFIG_PRINCIPAL = "rpa_email.json"
CARPETA_CONFIGS = "configuraciones_guardadas"
SCHEMA_FILE = "schemas/rpa_email.schema.json"