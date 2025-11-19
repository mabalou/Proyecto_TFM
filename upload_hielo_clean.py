import pandas as pd
from pymongo import MongoClient

# ------------------------------
# 1) Cargar CSV limpio
# ------------------------------
df = pd.read_csv("data/socioeconomico/co2_emissions_by_country.csv")
df.columns = df.columns.str.strip().str.lower()

# Detectar columnas correctas
year_col = next((c for c in df.columns if "year" in c), None)
country_col = next((c for c in df.columns if "country" in c), None)
emission_col = next((c for c in df.columns if "co2" in c or "emission" in c), None)

df = df.rename(columns={
    year_col: "Year",
    country_col: "Country",
    emission_col: "CO2_Emissions_Mt"
})

df = df[["Year", "Country", "CO2_Emissions_Mt"]].dropna()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df["CO2_Emissions_Mt"] = pd.to_numeric(df["CO2_Emissions_Mt"], errors="coerce")

# ------------------------------
# 2) Conexión a MongoDB
# ------------------------------
uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["tfm_datos"]
collection = db["co2_emissions_global"]

collection.drop()  # borrar si existe
collection.insert_many(df.to_dict(orient="records"))

print("✔ Datos subidos correctamente a MongoDB.")
