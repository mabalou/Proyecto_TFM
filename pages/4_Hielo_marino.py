import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# ----------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ----------------------------
st.set_page_config(page_title="🧊 Evolución del hielo marino", layout="wide")
st.title("🧊 Evolución del hielo marino")
st.markdown("Visualiza y analiza la extensión del hielo marino en el Ártico y el Antártico desde 1978 de forma interactiva.")

# ----------------------------
# CARGA DE DATOS
# ----------------------------
@st.cache_data
def cargar_datos(region):
    if region == "Ártico":
        archivo = "data/hielo/arctic_sea_ice_extent.csv"
    else:
        archivo = "data/hielo/antarctic_sea_ice_extent.csv"

    df = pd.read_csv(archivo)

    # Renombrar columnas según idioma real del CSV
    df = df.rename(columns={
        "Year": "Año",
        "Month": "Mes",
        "Extent": "Extensión"
    })

    # Validar columnas disponibles
    columnas_presentes = [col for col in ["Año", "Mes", "Extensión"] if col in df.columns]
    if "Año" not in columnas_presentes or "Extensión" not in columnas_presentes:
        raise ValueError(f"El archivo {archivo} no contiene las columnas esperadas. Columnas detectadas: {list(df.columns)}")

    df = df[columnas_presentes].dropna()

    # Convertir a numérico
    for col in columnas_presentes:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Agrupar por año (promedio anual)
    df_anual = df.groupby("Año")["Extensión"].mean().reset_index()

    return df_anual

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.header("🧭 Selecciona la región")
region = st.sidebar.radio("Elige una región:", ["Ártico", "Antártico"])

df = cargar_datos(region)

# ----------------------------
# SIDEBAR PERSONALIZACIÓN
# ----------------------------
st.sidebar.header("🔧 Personaliza la visualización")

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1990, max_year))
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ----------------------------
# FILTRADO DE DATOS
# ----------------------------
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ----------------------------
# VISUALIZACIÓN PRINCIPAL
# ----------------------------
if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Año", y="Extensión", markers=True,
                  labels={"Año": "Año", "Extensión": "Extensión (millones km²)"},
                  title=f"Evolución del hielo marino - {region}")
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Año", y="Extensión",
                  labels={"Año": "Año", "Extensión": "Extensión (millones km²)"},
                  title=f"Evolución del hielo marino - {region}")
else:
    fig = px.bar(df_filtrado, x="Año", y="Extensión",
                 labels={"Año": "Año", "Extensión": "Extensión (millones km²)"},
                 title=f"Evolución del hielo marino - {region}")

# Línea de tendencia
if mostrar_tendencia:
    x = df_filtrado["Año"].values
    y = df_filtrado["Extensión"].values
    coef = np.polyfit(x, y, 1)
    tendencia = coef[0] * x + coef[1]
    fig.add_scatter(x=x, y=tendencia, mode="lines", name="Tendencia",
                    line=dict(color="red", dash="dash", width=2))

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# TEXTO TENDENCIA
# ----------------------------
if mostrar_tendencia:
    st.markdown(f"🧭 **La tendencia muestra un cambio de aproximadamente `{coef[0]:.4f}` millones km² por año.**")

# ----------------------------
# MÉTRICAS DESTACADAS
# ----------------------------
st.subheader("🔎 Indicadores destacados")
max_ext = df_filtrado["Extensión"].max()
min_ext = df_filtrado["Extensión"].min()
año_max = df_filtrado[df_filtrado["Extensión"] == max_ext]["Año"].values[0]
año_min = df_filtrado[df_filtrado["Extensión"] == min_ext]["Año"].values[0]
st.markdown(f"**📈 Máxima extensión:** {max_ext:.2f} millones km² en {año_max}")
st.markdown(f"**📉 Mínima extensión:** {min_ext:.2f} millones km² en {año_min}")

# ----------------------------
# MEDIA POR DÉCADAS
# ----------------------------
if mostrar_decadas:
    st.subheader("📊 Media de extensión por década")
    df_decada = df_filtrado.copy()
    df_decada["Década"] = (df_decada["Año"] // 10) * 10
    df_grouped = df_decada.groupby("Década")["Extensión"].mean().reset_index()
    df_grouped["Década"] = df_grouped["Década"].astype(int)

    st.dataframe(df_grouped.style.format("{:.2f}"))

    fig_dec = px.bar(df_grouped, x="Década", y="Extensión",
                     labels={"Extensión": "Media (millones km²)", "Década": "Década"},
                     barmode="group",
                     title=f"Extensión media por década - {region}")
    st.plotly_chart(fig_dec, use_container_width=True)

# ----------------------------
# MODELO PREDICTIVO (hasta 2100)
# ----------------------------
if mostrar_prediccion:
    st.subheader("🔮 Predicción de la extensión hasta 2100")

    x = df["Año"].values
    y = df["Extensión"].values
    coef_pred = np.polyfit(x, y, 2)
    x_pred = np.arange(x.max()+1, 2101)
    y_pred = np.polyval(coef_pred, x_pred)

    fig_pred = px.line(x=x_pred, y=y_pred, labels={"x": "Año", "y": "Extensión (millones km²)"},
                       title=f"Predicción futura del hielo marino ({region}) hasta 2100")
    st.plotly_chart(fig_pred, use_container_width=True)

# ----------------------------
# DESCARGAS
# ----------------------------
st.subheader("💾 Descargar")
col1, col2 = st.columns(2)

with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv,
                       file_name=f"hielo_marino_{region.lower()}.csv", mime="text/csv")

with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer,
                       file_name=f"grafico_hielo_marino_{region.lower()}.png", mime="image/png")
