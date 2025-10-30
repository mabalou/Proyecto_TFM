import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------
# TÍTULO PRINCIPAL
# ----------------------------
st.set_page_config(page_title="Visualizador climático", layout="centered")
st.title("🌡️ Evolución de la temperatura global")
st.markdown("Este gráfico muestra la evolución de la anomalía de la temperatura global a lo largo del tiempo, usando datos de la NASA GISTEMP.")

# ----------------------------
# CARGA DE DATOS
# ----------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)
    df = df[["Year", "J-D"]]  # Solo nos interesa el año y la media anual
    df = df.dropna()  # Eliminamos posibles valores nulos
    df["J-D"] = df["J-D"].astype(float)  # Aseguramos tipo numérico
    return df

df_temp = cargar_datos()

# ----------------------------
# VISUALIZACIÓN
# ----------------------------
fig = px.line(
    df_temp,
    x="Year",
    y="J-D",
    labels={"Year": "Año", "J-D": "Anomalía media anual (°C)"},
    title="Anomalía de temperatura global (NASA GISTEMP)",
)
fig.update_traces(mode="lines+markers")
fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

st.plotly_chart(fig, use_container_width=True)
