import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# ----------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ----------------------------
st.set_page_config(page_title="🌡️ Visualizador climático TFM", layout="wide")
st.title("🌍 Evolución de la temperatura global")
st.markdown("Visualiza y analiza los datos de anomalía de temperatura global (NASA GISTEMP) de forma interactiva.")

# ----------------------------
# CARGA DE DATOS
# ----------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)
    df = df[["Year", "J-D", "DJF", "MAM", "JJA", "SON"]]
    df = df.replace("***", np.nan)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    return df

df = cargar_datos()

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.header("🔧 Personaliza la visualización")

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1970, max_year))
series_disponibles = ["J-D", "DJF", "MAM", "JJA", "SON"]
series_seleccionadas = st.sidebar.multiselect("Variables a visualizar", series_disponibles, default=["J-D"])
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ----------------------------
# FILTRADO DE DATOS
# ----------------------------
df_filtrado = df[(df["Year"] >= rango[0]) & (df["Year"] <= rango[1])]

# ----------------------------
# VISUALIZACIÓN PRINCIPAL
# ----------------------------
if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Year", y=series_seleccionadas, markers=True,
                  labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"},
                  title="Anomalía de temperatura global")
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Year", y=series_seleccionadas,
                  labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"},
                  title="Anomalía de temperatura global")
else:
    fig = px.bar(df_filtrado, x="Year", y=series_seleccionadas,
                 labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"},
                 title="Anomalía de temperatura global")

# Añadir tendencia si aplica
if mostrar_tendencia and len(series_seleccionadas) == 1:
    y = df_filtrado[series_seleccionadas[0]].values
    x = df_filtrado["Year"].values
    coef = np.polyfit(x, y, 1)
    tendencia = coef[0] * x + coef[1]
    fig.add_scatter(x=x, y=tendencia, mode="lines", name="Tendencia",
                    line=dict(color="red", dash="dash", width=2))

st.plotly_chart(fig, use_container_width=True)

# ➤ Mostrar análisis debajo del gráfico
if mostrar_tendencia and len(series_seleccionadas) == 1:
    st.markdown(f"🧭 **La tendencia muestra un aumento de aproximadamente `{coef[0]:.4f} °C` por año.**")

# ----------------------------
# MÉTRICAS DESTACADAS
# ----------------------------
st.subheader("🔎 Indicadores destacados")
for serie in series_seleccionadas:
    max_anomalia = df_filtrado[serie].max()
    min_anomalia = df_filtrado[serie].min()
    año_max = df_filtrado[df_filtrado[serie] == max_anomalia]["Year"].values[0]
    año_min = df_filtrado[df_filtrado[serie] == min_anomalia]["Year"].values[0]
    st.markdown(f"**{serie}** — Máx: {max_anomalia:.2f} °C en {año_max}, Mín: {min_anomalia:.2f} °C en {año_min}")

# ----------------------------
# ANÁLISIS POR DÉCADAS
# ----------------------------
if mostrar_decadas:
    st.subheader("📊 Media de anomalías por década")
    df_decada = df_filtrado.copy()
    df_decada["Década"] = (df_decada["Year"] // 10) * 10
    df_grouped = df_decada.groupby("Década")[series_seleccionadas].mean().reset_index()
    df_grouped["Década"] = df_grouped["Década"].astype(int)
    st.dataframe(df_grouped.style.format("{:.2f}"))

    fig_dec = px.bar(df_grouped, x="Década", y=series_seleccionadas,
                     labels={"value": "Anomalía promedio (°C)", "variable": "Variable"},
                     barmode="group",
                     title="Anomalías medias por década")
    st.plotly_chart(fig_dec, use_container_width=True)

# ----------------------------
# MODELO PREDICTIVO (hasta 2100)
# ----------------------------
if mostrar_prediccion and len(series_seleccionadas) == 1:
    st.subheader("🔮 Predicción de anomalía hasta 2100")

    serie = series_seleccionadas[0]
    x = df["Year"].values
    y = df[serie].values

    # Modelo polinómico de grado 2
    coef = np.polyfit(x, y, 2)
    x_pred = np.arange(x.max()+1, 2101)
    y_pred = np.polyval(coef, x_pred)

    fig_pred = px.line(x=x_pred, y=y_pred, labels={"x": "Año", "y": "Anomalía (°C)"},
                       title="Predicción futura de anomalía de temperatura")
    st.plotly_chart(fig_pred, use_container_width=True)

# ----------------------------
# DESCARGAS
# ----------------------------
st.subheader("💾 Descargar")

col1, col2 = st.columns(2)

with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="temperatura_filtrada.csv", mime="text/csv")

with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer, file_name="grafico_temperatura.png", mime="image/png")
