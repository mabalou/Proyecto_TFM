import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

# ----------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ----------------------------
st.set_page_config(page_title="🌍 Gases de Efecto Invernadero", layout="wide")
st.title("🌍 Evolución de los gases de efecto invernadero")
st.markdown("Visualiza y analiza la concentración global de CO₂, CH₄ y N₂O en la atmósfera de forma interactiva.")

# ----------------------------
# CARGA DE DATOS
# ----------------------------
@st.cache_data
def cargar_datos_gas(ruta_csv):
    with open(ruta_csv, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Buscar línea del encabezado
    for i, linea in enumerate(lineas):
        if "year,month,decimal" in linea.replace("\t", ""):
            encabezado_index = i
            break

    # Cargar datos desde la línea del encabezado
    df = pd.read_csv(ruta_csv, skiprows=encabezado_index)
    df = df.rename(columns=lambda x: x.strip())
    df = df[["year", "decimal", "average", "trend"]]
    df = df.rename(columns={
        "year": "Año",
        "decimal": "Año_decimal",
        "average": "Concentración",
        "trend": "Tendencia"
    })
    df = df.dropna(subset=["Año", "Concentración"])
    df["Año"] = df["Año"].astype(int)
    return df

# Rutas de tus CSV
RUTAS = {
    "CO₂ (ppm)": "data/gases/greenhouse_gas_co2_global.csv",
    "CH₄ (ppb)": "data/gases/greenhouse_gas_ch4_global.csv",
    "N₂O (ppb)": "data/gases/greenhouse_gas_n2o_global.csv"
}

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.header("🔧 Personaliza la visualización")
gas = st.sidebar.selectbox("Selecciona un gas", list(RUTAS.keys()))
tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ----------------------------
# CARGA Y FILTRADO
# ----------------------------
df = cargar_datos_gas(RUTAS[gas])
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
rango = st.sidebar.slider("Rango de años", min_year, max_year, (2000, max_year))
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ----------------------------
# VISUALIZACIÓN
# ----------------------------
titulo = f"Evolución global de {gas} en la atmósfera"
eje_y = f"Concentración ({'ppm' if 'CO₂' in gas else 'ppb'})"

if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Año", y="Concentración", markers=True,
                  labels={"Año": "Año", "Concentración": eje_y},
                  title=titulo)
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Año", y="Concentración",
                  labels={"Año": "Año", "Concentración": eje_y},
                  title=titulo)
else:
    fig = px.bar(df_filtrado, x="Año", y="Concentración",
                 labels={"Año": "Año", "Concentración": eje_y},
                 title=titulo)

# Añadir línea de tendencia
if mostrar_tendencia:
    x = df_filtrado["Año"].values.reshape(-1, 1)
    y = df_filtrado["Concentración"].values
    modelo = LinearRegression()
    modelo.fit(x, y)
    y_pred = modelo.predict(x)
    fig.add_scatter(x=df_filtrado["Año"], y=y_pred,
                    mode="lines", name="Tendencia",
                    line=dict(color="red", dash="dash", width=2))

# Mostrar el gráfico
st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# ANÁLISIS DE TENDENCIA
# ----------------------------
if mostrar_tendencia:
    pendiente = modelo.coef_[0]
    st.markdown(f"🧭 **La tendencia muestra un cambio de aproximadamente `{pendiente:.4f}` unidades por año.**")

# ----------------------------
# MODELO PREDICTIVO
# ----------------------------
if mostrar_prediccion:
    st.subheader("🔮 Predicción de concentración hasta 2100")
    x_full = df["Año"].values.reshape(-1, 1)
    y_full = df["Concentración"].values
    modelo_pred = LinearRegression()
    modelo_pred.fit(x_full, y_full)

    años_futuros = np.arange(df["Año"].max() + 1, 2101).reshape(-1, 1)
    predicciones = modelo_pred.predict(años_futuros)

    fig_pred = px.line(x=años_futuros.ravel(), y=predicciones,
                       labels={"x": "Año", "y": eje_y},
                       title="Predicción futura de concentración")
    st.plotly_chart(fig_pred, use_container_width=True)

# ----------------------------
# DESCARGAS
# ----------------------------
st.subheader("💾 Descargar")

col1, col2 = st.columns(2)

with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv,
                       file_name=f"{gas.replace(' ', '_')}_filtrado.csv", mime="text/csv")

with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer,
                       file_name=f"{gas.replace(' ', '_')}_grafico.png", mime="image/png")
