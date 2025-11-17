import time
import requests
import pandas as pd
import os

ESTACIONES = [
    ("centro",   "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=CENTRO"),
    ("sureste",  "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SURESTE"),
    ("noreste",  "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORESTE"),
    ("noroeste", "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NOROESTE"),
    ("suroeste", "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SUROESTE"),
    ("noroeste2","https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=GARCIA"),
    ("norte",    "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORTE"),
    ("noreste2", "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORESTE2"),
    ("sureste2", "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SURESTE2"),
    ("suroeste2","https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=[SAN Pedro]"),
    ("sureste3", "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SURESTE3"),
    ("norte2",   "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORTE2"),
    ("sur",      "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SUR"),
    ("este",     "https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=PESQUERIA"),
    ("noroeste3","https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NOROESTE3"),
]

BASE_API = "https://aire.nl.gob.mx/SIMA2017reportes/api_indice.php"

CSV_ANCHO_ACTUAL    = "aire_indice_api_ancho.csv"
CSV_ANCHO_HISTORICO = "aire_indice_api_ancho_historico.csv"


def obtener_indice_estacion(slug: str, url_reporte: str) -> pd.DataFrame:
    s = requests.Session()
    s.get(url_reporte, timeout=10)

    params = {"t": int(time.time() * 1000)}
    r = s.get(BASE_API, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()
    df = pd.DataFrame(data)

    df["HrAveData"] = pd.to_numeric(df["HrAveData"], errors="coerce")
    df.insert(0, "Estacion", slug)
    df = df[["Estacion", "Parameter", "Date", "HrAveData"]]
    return df


def construir_tabla_ancha() -> pd.DataFrame:
    tablas = []
    for slug, url in ESTACIONES:
        try:
            print(f"→ Obteniendo: {slug}")
            df_e = obtener_indice_estacion(slug, url)
            tablas.append(df_e)
        except Exception as e:
            print(f"⚠ Error con {slug}: {e}")

    if not tablas:
        return pd.DataFrame()

    df = pd.concat(tablas, ignore_index=True)

    df_wide = df.pivot_table(
        index=["Estacion", "Date"],
        columns="Parameter",
        values="HrAveData",
        aggfunc="first"
    ).reset_index()

    df_wide.columns.name = None

    base_cols = ["Estacion", "Date"]
    params_cols = sorted([c for c in df_wide.columns if c not in base_cols])
    df_wide = df_wide[base_cols + params_cols]

    df_wide["estatus"] = df_wide[params_cols].notna().all(axis=1)
    df_wide["estatus"] = df_wide["estatus"].map({True: "completo", False: "incompleto"})

    return df_wide


def actualizar_historico(df_nuevo: pd.DataFrame):
    df_nuevo = df_nuevo.copy()
    df_nuevo["Date"] = pd.to_datetime(df_nuevo["Date"])

    if os.path.exists(CSV_ANCHO_HISTORICO):
        hist = pd.read_csv(CSV_ANCHO_HISTORICO)
        if not hist.empty:
            hist["Date"] = pd.to_datetime(hist["Date"])
            df_hist = pd.concat([hist, df_nuevo], ignore_index=True)
        else:
            df_hist = df_nuevo
    else:
        df_hist = df_nuevo

    df_hist.drop_duplicates(subset=["Estacion", "Date"], keep="last", inplace=True)
    df_hist.sort_values(["Estacion", "Date"], inplace=True)
    df_hist.reset_index(drop=True, inplace=True)

    df_hist.to_csv(CSV_ANCHO_HISTORICO, index=False, encoding="utf-8-sig")
    return df_hist


if __name__ == "__main__":
    df_wide = construir_tabla_ancha()

    print("\nPreview tabla ancha:")
    print(df_wide.head())

    df_wide.to_csv(CSV_ANCHO_ACTUAL, index=False, encoding="utf-8-sig")
    print(f"\n✔ Guardado último corte: {CSV_ANCHO_ACTUAL}")

    df_hist = actualizar_historico(df_wide)
    print(f"✔ Histórico actualizado: {CSV_ANCHO_HISTORICO}")
    print(f"Total de registros históricos: {len(df_hist)}")
