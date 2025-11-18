import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --------------------------------------------------------
# 1) Cargar el CSV generado por el primer código (main.py)
# --------------------------------------------------------

CSV_FILE = "aire_monterrey.csv"   # Archivo de la tabla con Calidad / Riesgo

if not os.path.exists(CSV_FILE):
    print(f"❌ No se encontró el archivo {CSV_FILE}. No se enviarán alertas.")
    raise SystemExit()

df = pd.read_csv(CSV_FILE)

# --------------------------------------------------------
# 2) Filtrar estaciones con mala calidad
#    (Mala, Muy mala, Extremadamente mala)
# --------------------------------------------------------

niveles_alerta = ["Mala", "Muy mala", "Extremadamente mala"]

if "Calidad" not in df.columns:
    print("❌ La columna 'Calidad' no existe en el CSV. Revisa main.py.")
    raise SystemExit()

df_alertas = df[df["Calidad"].isin(niveles_alerta)].copy()

if df_alertas.empty:
    print("✔ No hay estaciones con calidad crítica. No se enviará correo.")
    raise SystemExit()

print(f"⚠ Se encontraron {len(df_alertas)} estaciones con alerta.")

# --------------------------------------------------------
# 3) Función para generar semáforo visual
# --------------------------------------------------------

def calidad_badge(calidad: str) -> str:
    """
    Devuelve un span HTML con color y emoji tipo semáforo según la calidad.
    """
    mapping = {
        "Buena":               ("🟢", "#2e7d32"),
        "Aceptable":           ("🟡", "#fbc02d"),
        "Mala":                ("🟠", "#fb8c00"),
        "Muy mala":            ("🔴", "#e53935"),
        "Extremadamente mala": ("🟣", "#8e24aa"),
    }
    emoji, color = mapping.get(calidad, ("⚪", "#757575"))

    style = (
        f"background-color:{color};"
        "color:white;"
        "padding:3px 8px;"
        "border-radius:12px;"
        "font-size:12px;"
        "font-weight:bold;"
        "display:inline-block;"
        "min-width:110px;"
        "text-align:center;"
    )

    return f'<span style="{style}">{emoji} {calidad}</span>'

# --------------------------------------------------------
# 4) Construir tabla HTML bonita con semáforos
# --------------------------------------------------------

# Nos quedamos con columnas clave (y solo las que existan)
cols_deseadas = [
    "Estacion",
    "Municipio",
    "contaminante",
    "concentracion",
    "Calidad",
    "Riesgo",
    "Date",
    "url_reporte",
]

cols_presentes = [c for c in cols_deseadas if c in df_alertas.columns]
df_alertas = df_alertas[cols_presentes]

# Construimos manualmente la tabla para poder meter el badge HTML
cabeceras = {
    "Estacion": "Estación",
    "Municipio": "Municipio",
    "contaminante": "Contaminante",
    "concentracion": "Valor índice (Concentración)",
    "Calidad": "Calidad (semáforo)",
    "Riesgo": "Riesgo",
    "Date": "Fecha / hora",
    "url_reporte": "Reporte detalle",
}

# Encabezado de la tabla
thead_cells = "".join(
    f"<th style='border:1px solid #ddd;padding:6px 10px;background:#f5f5f5;'>{cabeceras.get(col, col)}</th>"
    for col in cols_presentes
)
thead_html = f"<thead><tr>{thead_cells}</tr></thead>"

# Filas
rows_html = ""
for _, row in df_alertas.iterrows():
    celdas = []
    for col in cols_presentes:
        val = row[col]

        if col == "Calidad":
            # Cambiar texto por badge de color
            cell_html = calidad_badge(str(val))
        elif col == "url_reporte" and isinstance(val, str):
            # Hacer la URL clickeable
            cell_html = f"<a href='{val}' target='_blank'>Ver reporte</a>"
        else:
            cell_html = str(val)

        celdas.append(
            f"<td style='border:1px solid #ddd;padding:6px 10px;text-align:center;'>{cell_html}</td>"
        )

    rows_html += f"<tr>{''.join(celdas)}</tr>"

tabla_html = f"""
<table style="border-collapse:collapse;width:100%;max-width:900px;margin-top:10px;">
  {thead_html}
  <tbody>
    {rows_html}
  </tbody>
</table>
"""

# --------------------------------------------------------
# 5) Preparar correo
# --------------------------------------------------------

SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
ALERT_TO_EMAIL = os.environ.get("ALERT_TO_EMAIL")

if not SMTP_USER or not SMTP_PASS or not ALERT_TO_EMAIL:
    print("❌ Faltan secretos: SMTP_USER, SMTP_PASS o ALERT_TO_EMAIL")
    raise SystemExit()

msg = MIMEMultipart("alternative")
msg["Subject"] = "⚠ Alertas de Calidad del Aire - Estaciones en Riesgo"
msg["From"] = SMTP_USER
msg["To"] = ALERT_TO_EMAIL

html_body = f"""
<html>
  <body style="font-family:Arial, sans-serif; font-size:14px; color:#333;">
    <h2 style="color:#d32f2f;">⚠ Estaciones con calidad del aire crítica</h2>
    <p>
      Se detectaron estaciones cuyo nivel de calidad del aire es
      <b>Mala</b>, <b>Muy mala</b> o <b>Extremadamente mala</b>.
    </p>
    {tabla_html}
    <br>
    <p style="font-size:12px;color:#777;">
      Reporte generado automáticamente desde GitHub Actions.<br>
      Archivo base: <code>{CSV_FILE}</code>
    </p>
  </body>
</html>
"""

msg.attach(MIMEText(html_body, "html", "utf-8"))

# --------------------------------------------------------
# 6) Enviar correo via SMTP (Gmail)
# --------------------------------------------------------

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [ALERT_TO_EMAIL], msg.as_string())

    print("📧 Alerta enviada correctamente.")

except Exception as e:
    print("❌ Error enviando el correo:")
    print(e)
