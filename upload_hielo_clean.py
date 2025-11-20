import pandas as pd
from pymongo import MongoClient

# -----------------------
# Función de normalización GENÉRICA
# -----------------------
def normaliza(df, country_col, year_col, value_col):
    df = df.rename(columns={
        country_col: "Country",
        year_col: "Year",
        value_col: "Value"
    })[["Country", "Year", "Value"]]

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Country", "Year", "Value"])
    return df


# -----------------------
# Conexión MongoDB
# -----------------------
uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["tfm_datos"]

def subir(df, nombre):
    registros = df.to_dict(orient="records")
    db[nombre].delete_many({})
    db[nombre].insert_many(registros)
    print(f"✔ Subido correctamente: {nombre} ({len(registros)} documentos)")


# -----------------------
# 2) CH₄ (Metano)
# -----------------------
df_ch4 = pd.read_csv("data/gases/methane-emissions.csv")
df_ch4.columns = df_ch4.columns.str.lower()

# buscar automáticamente la columna de metano
col_methane = "methane"
if col_methane not in df_ch4.columns:
    col_methane = [c for c in df_ch4.columns if "methane" in c][0]

df_ch4_clean = normaliza(df_ch4, "entity", "year", col_methane)
subir(df_ch4_clean, "gases_ch4_by_country")


# -----------------------
# 3) N₂O (Óxido nitroso)
# -----------------------
df_n2o = pd.read_csv("data/gases/nitrous-oxide-emissions.csv")
df_n2o.columns = df_n2o.columns.str.lower()

col_n2o = "nitrous oxide"
if col_n2o not in df_n2o.columns:
    col_n2o = [c for c in df_n2o.columns if "nitrous" in c][0]

df_n2o_clean = normaliza(df_n2o, "entity", "year", col_n2o)
subir(df_n2o_clean, "gases_n2o_by_country")
