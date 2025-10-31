import pandas as pd

def cargar_temperatura_global():
    """
    Carga y limpia los datos de temperatura global de la NASA GISTEMP.
    """
    df = pd.read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)

    # Nos aseguramos de eliminar los valores no numéricos como '***'
    df.replace('***', None, inplace=True)
    df = df[["Year", "J-D", "DJF", "MAM", "JJA", "SON"]]  # Incluimos estaciones
    df = df.dropna()

    # Convertimos a valores numéricos
    for col in ["J-D", "DJF", "MAM", "JJA", "SON"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna()
    return df
