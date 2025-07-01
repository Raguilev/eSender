PLANTILLA_HTML_POR_DEFECTO = """
<p>Estimado equipo,</p>

<p>Se ha generado correctamente el siguiente reporte automático desde la plataforma <b>{{nombre_rpa}}</b>.</p>

<p><b>Fecha y hora de captura:</b> {{fecha}}</p>

<p><b>Vista previa del panel:</b></p>
<img src="cid:screenshot" alt="Panel" />

<p><b>Última URL visitada:</b> <a href="{{url_dashboard}}" target="_blank">{{url_dashboard}}</a></p>

<p><b>Secuencia completa de URLs visitadas:</b></p>
{{lista_urls}}

<br><p><small>Este mensaje fue generado automáticamente por el sistema RPA.</small></p>
"""

RUTA_CONFIG_PRINCIPAL = "rpa_email.json"
RUTA_CARPETA_RESPALDOS = "configuraciones_guardadas"
SCHEMA_FILE = "schemas/rpa_email.schema.json"