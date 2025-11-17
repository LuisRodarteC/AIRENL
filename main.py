import pandas as pd
import requests
import re
import json

def imprimir_tabla_pandas(datos):
    df = pd.DataFrame(datos)
    print(df)

URL = "https://aire.nl.gob.mx/airemapbing/airebing_icars_alt_ns_newNL_4.php"

def obtener_arrayIMKTodo11():
    # 1. Descargar HTML+JS
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    html = resp.text

    # 2. Buscar el arreglo JS: var/let/const arrayIMKTodo11 = [ {...}, ... ]
    patron = r"(?:var|let|const)\s+arrayIMKTodo11\s*=\s*(\[\s*{.*?}\s*\])"
    match = re.search(patron, html, re.DOTALL)
    if not match:
        raise RuntimeError("No se encontró arrayIMKTodo11 en la respuesta.")

    json_str = match.group(1)

    # --- DEBUG opcional: ver un pedacito de lo que vamos a parsear ---
    # print("Primeros 300 caracteres del JSON candidato:\n", json_str[:300])

    # 3. Arreglos para que sea JSON válido

    # 3.1. Reemplazar Null (JS) por null (JSON)
    json_str = json_str.replace("Null", "null")

    # 3.2. Quitar comas sobrantes antes de '}' o ']'
    #     Ejemplo: {"a":1,}  -> {"a":1}
    #              [ {...}, ] -> [ {...} ]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    # 4. Convertir a lista de dicts de Python
    try:
        datos = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ Error al decodificar JSON:")
        print("Mensaje:", e)
        print("Longitud de json_str:", len(json_str))
        print("Fragmento inicial:\n", json_str[:500])
        raise

    return datos

def imprimir_tabla(datos):
    columnas = ["Estacion", "Parameter", "contaminante", "HrAveData", "concentracion", "Date"]

    # Encabezados
    print("\t".join(columnas))

    # Filas
    for fila in datos:
        valores = [str(fila.get(col, "")) for col in columnas]
        print("\t".join(valores))

if __name__ == "__main__":
    datos = obtener_arrayIMKTodo11()

    #print(f"✔ arrayIMKTodo11 leído correctamente. Registros: {len(datos)}\n")
    #imprimir_tabla_pandas(datos)

df = pd.DataFrame(datos)

def get_calidad(valor):
    if valor < 51:
        return 'Buena'
    if valor < 101:
        return 'Aceptable'
    if valor < 151:
        return 'Mala'
    if valor < 201:
        return 'Muy mala'
    return 'Extremadamente mala'

def get_riesgo(valor):
    if valor < 51:
        return 'Bajo'
    if valor < 101:
        return 'Moderado'
    if valor < 151:
        return 'Alto'
    if valor < 201:
        return 'Muy alto'
    return 'Extremo'

# Aplicar las funciones a la columna HrAveData
df["Calidad"] = df["HrAveData"].apply(get_calidad)
df["Riesgo"]  = df["HrAveData"].apply(get_riesgo)

#print(df)

locations = [['CENTRO', 25.6760139, -100.338553, 4, 'Monterrey', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=CENTRO', 'centro', 'CE'],
             ['SURESTE', 25.6654972, -100.243653, 2, 'Guadalupe', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SURESTE', 'sureste', 'SE'],
             ['NORESTE', 25.74503, -100.25317, 3, 'San Nicolás', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORESTE', 'noreste', 'NE'],
             ['NOROESTE', 25.7629306, -100.369578, 5, 'Monterrey', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NOROESTE', 'noroeste', 'NO'],
             ['SUROESTE', 25.6794444, -100.467831, 6, 'Santa Catarina', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SUROESTE', 'suroeste', 'SO'],
             ['NOROESTE 2', 25.8004639, -100.585011, 7, 'García', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=GARCIA', 'noroeste2', 'NO2'],
             ['NORTE', 25.7988361, -100.327164, 8, 'Escobedo', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORTE', 'norte', 'N'],
             ['NORESTE 2', 25.777475, -100.1882, 1, 'Apodaca', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORESTE2', 'noreste2', 'NE2'],
             ['SURESTE 2', 25.646126, -100.095616, 9, 'Juárez', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SURESTE2', 'sureste2', 'SE2'],
             ['SUROESTE 2', 25.665275, -100.412853, 10, 'San Pedro', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=[SAN Pedro]', 'suroeste2', 'SO2'],
             ['SURESTE 3', 25.6008639, -99.9953028, 11, 'Cadereyta', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SURESTE3', 'sureste3', 'SE3'],
             ['NORTE 2', 25.7297587, -100.310019, 12, 'San Nicolás', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NORTE2', 'norte2', 'N2'],
             ['SUR', 25.6169806, -100.273936, 13, 'Monterrey', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=SUR', 'sur', 'S'],
             ['ESTE', 25.7905833, -100.078411, 14, 'Pesqueria', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=PESQUERIA', 'este', 'NE3'],
             ['NOROESTE 3', 25.785, -100.46361112, 15, 'García', 'https://aire.nl.gob.mx/SIMA2017reportes/ReporteDiariosimaIcars.php?estacion1=NOROESTE3', 'noroeste3', 'NO3']]

cols_loc = ["Nombre", "Lat", "Lon", "id", "Municipio", "url_reporte", "slug", "codigo"]

loc_df = pd.DataFrame(locations, columns=cols_loc)
df = df.merge(
    loc_df[["slug", "Lat", "Lon", "Municipio", "url_reporte"]],
    left_on="Estacion",
    right_on="slug",
    how="left"
).drop(columns=["slug"])

#print(df[["Estacion", "HrAveData", "Calidad", "Riesgo", "Lat", "Lon", "Municipio"]])

df.to_csv("aire_monterrey.csv", index=False)
