import pandas as pd
from pymongo import MongoClient
import os

# -----------------------------
# CONFIGURACIÓN MONGO
# -----------------------------
PASSWORD = "parausarentfm123"
URI = f"mongodb+srv://marcosabal:{PASSWORD}@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority&appName=tfmcc"

client = MongoClient(URI)
db = client["tfm_datos"]
print(f"Conectado a MongoDB — Base de datos: tfm_datos")

# -----------------------------
# LISTA DE ARCHIVOS A SUBIR
# -----------------------------
ARCHIVOS = {
    "hielo_antarctic_sea_ice_extent": "data/hielo/antarctic_sea_ice_extent.csv",
    "hielo_arctic_sea_ice_extent": "data/hielo/arctic_sea_ice_extent.csv",
    "temperatura_global_temperature_nasa": "data/temperatura/global_temperature_nasa.csv",
    "gases_greenhouse_gas_n2o_global": "data/gases/greenhouse_gas_n2o_global.csv",
    "gases_greenhouse_gas_ch4_global": "data/gases/greenhouse_gas_ch4_global.csv",
    "gases_greenhouse_gas_co2_global": "data/gases/greenhouse_gas_co2_global.csv",
    "energia_energy_consuption_by_source": "data/energia/energy_consuption_by_source.csv",
    "sea_level_sea_level_nasa": "data/sea_level/sea_level_nasa.csv",
    "socioeconomico_exploratory_dashboard_data": "data/socioeconomico/exploratory_dashboard_data.csv",
    "socioeconomico_gdp_by_country": "data/socioeconomico/gdp_by_country.csv",
    "socioeconomico_co2_emissions_by_country": "data/socioeconomico/co2_emissions_by_country.csv",
    "socioeconomico_population_by_country": "data/socioeconomico/population_by_country.csv",
}

# -----------------------------
# CARGA GENERAL (SIN LIMPIEZA)
# -----------------------------
def subir_csv(nombre_coleccion, ruta):
    print(f"\n→ Procesando archivo: {ruta}")

    if not os.path.exists(ruta):
        print(f"   ❌ Archivo no encontrado: {ruta}")
        return

    try:
        df = pd.read_csv(ruta, encoding="utf-8", engine="python")
    except Exception as e:
        print(f"   ⚠ Error leyendo CSV con utf-8, reintentando en ISO-8859-1…")
        try:
            df = pd.read_csv(ruta, encoding="ISO-8859-1", engine="python")
        except Exception as e2:
            print(f"   ❌ Error final leyendo CSV: {e2}")
            return

    # Conversión a diccionarios
    registros = df.to_dict(orient="records")

    # Limpiar colección previa
    db[nombre_coleccion].drop()

    # Insertar datos
    if registros:
        db[nombre_coleccion].insert_many(registros)
        print(f"   ✔ Subido a colección: {nombre_coleccion} ({len(registros)} documentos)")
    else:
        print(f"   ⚠ CSV vacío, no subido: {nombre_coleccion}")


# -----------------------------
# EJECUCIÓN GENERAL
# -----------------------------
for coleccion, ruta in ARCHIVOS.items():
    subir_csv(coleccion, ruta)

print("\nOPERACIÓN COMPLETADA — Ya puedes ver los datos en Mongo Atlas")
