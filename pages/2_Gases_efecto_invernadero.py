import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from io import BytesIO

# ===========================
# CONFIGURACIÓN DE LA PÁGINA
# ===========================
st.set_page_config(page_title="Gases de efecto invernadero", layout="wide")
st.title("🌍 Evolución global de los gases de efecto invernadero")
st.write("Visualiza y analiza las concentraciones atmosféricas globales de CO₂, CH₄ y N₂O.")

# ===========================
# CARGA DE DATOS
# ===========================
@st.cache_data
def cargar_datos():
    ruta = "data/gases"
    dfs = []
    for archivo in os.listdir(ruta):
        if archivo.endswith(".csv"):
            path = os.path.join(ruta, archivo)
            # Intento de lectura flexible
            with open(path, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            # Buscar inicio de datos
            skip = 0
            for i, l in enumerate(lineas):
                if any(x.isdigit() for x in l):
                    skip = i
                    break
            df = pd.read_csv(path, skiprows=skip)
            df.columns = df.columns.str.strip().str.lower()
            # Detección del gas según archivo
            if "co2" in archivo.lower():
                df["gas"] = "CO₂"
            elif "ch4" in archivo.lower():
                df["gas"] = "CH₄"
            elif "n2o" in archivo.lower():
                df["gas"] = "N₂O"
            dfs.append(df)
    df_final = pd.concat(dfs, ignore_index=True)
    # Normalización de columnas
    if "year" in df_final.columns:
        df_final.rename(columns={"year": "Año"}, inplace=True)
    if "average" in df_final.columns:
        df_final.rename(columns={"average": "Concentración"}, inplace=True)
    df_final = df_final[["Año", "Concentración", "gas"]]
    df_final["Año"] = pd.to_numeric(df_final["Año"], errors="coerce")
    df_final.dropna(inplace=True)
    return df_final

df = cargar_datos()

# ===========================
# SIDEBAR
# ===========================
st.sidebar.header("🔧 Personaliza la visualización")
gas_seleccionado = st.sidebar.selectbox("Selecciona un gas:", df["gas"].unique())

min_año = int(df["Año"].min())
max_año = int(df["Año"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_año, max_año, (min_año, max_año))

mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo hasta 2100", False)

# ===========================
# FILTRADO Y AGRUPACIÓN
# ===========================
df_filtrado = df[df["gas"] == gas_seleccionado].copy()
df_filtrado = df_filtrado[(df_filtrado["Año"] >= rango[0]) & (df_filtrado["Año"] <= rango[1])]
df_filtrado = df_filtrado.groupby("Año", as_index=False)["Concentración"].mean()

# ===========================
# GRÁFICO PRINCIPAL
# ===========================
fig = go.Figure()

# Serie principal
fig.add_trace(go.Scatter(
    x=df_filtrado["Año"],
    y=df_filtrado["Concentración"],
    mode='lines+markers',
    name="Concentración",
    line=dict(color='skyblue', width=2),
    marker=dict(size=5)
))

# Línea de tendencia
pendiente = None
if mostrar_tendencia:
    tendencia = np.poly1d(np.polyfit(df_filtrado["Año"], df_filtrado["Concentración"], 1))
    pendiente = tendencia.coefficients[0]
    fig.add_trace(go.Scatter(
        x=df_filtrado["Año"],
        y=tendencia(df_filtrado["Año"]),
        mode='lines',
        name="Tendencia",
        line=dict(color='red', width=2, dash='dash')
    ))

# Modelo predictivo
if mostrar_prediccion:
    modelo = LinearRegression()
    X = df_filtrado[["Año"]]
    y = df_filtrado["Concentración"]
    modelo.fit(X, y)

    años_futuros = np.arange(df_filtrado["Año"].max() + 1, 2101)
    predicciones = modelo.predict(años_futuros.reshape(-1, 1))

    fig.add_trace(go.Scatter(
        x=años_futuros,
        y=predicciones,
        mode='lines',
        name="Predicción (modelo lineal)",
        line=dict(color='orange', width=2, dash='dot')
    ))

# Estilo general
fig.update_layout(
    title=f"Evolución global de {gas_seleccionado} en la atmósfera",
    xaxis_title="Año",
    yaxis_title="Concentración (ppm / ppb)",
    template="plotly_dark",
    height=550,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

# ===========================
# ANÁLISIS DESCRIPTIVO
# ===========================
st.subheader("🧠 Explicación analítica")

media = df_filtrado["Concentración"].mean()
año_max = df_filtrado.loc[df_filtrado["Concentración"].idxmax(), "Año"]
max_valor = df_filtrado["Concentración"].max()

texto = (
    f"Durante el período seleccionado ({rango[0]}–{rango[1]}), "
    f"la concentración media de {gas_seleccionado} fue de aproximadamente **{media:.2f} unidades**. "
    f"El valor máximo registrado fue de **{max_valor:.2f}** en el año **{año_max}**. "
)

if pendiente:
    texto += (
        f"La tendencia muestra un incremento medio anual de aproximadamente "
        f"**{pendiente:.4f} unidades por año**, lo que indica un crecimiento sostenido "
        f"en las concentraciones de {gas_seleccionado}."
    )
else:
    texto += "No se muestra la línea de tendencia en esta visualización."

st.markdown(texto)

# ===========================
# DESCARGAS
# ===========================
st.subheader("💾 Descargar datos")

csv = df_filtrado.to_csv(index=False).encode("utf-8")
st.download_button("📄 Descargar CSV filtrado", data=csv, file_name=f"{gas_seleccionado}_filtrado.csv", mime="text/csv")

# Descarga del gráfico
buffer = BytesIO()
fig.write_image(buffer, format="png")
st.download_button("🖼️ Descargar gráfico", data=buffer.getvalue(),
                   file_name=f"{gas_seleccionado}_grafico.png", mime="image/png")
