import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

# ----------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ----------------------------
st.set_page_config(page_title="🌊 Nivel del mar", layout="wide")
st.title("🌊 Evolución del nivel del mar global")
st.markdown("Visualiza y analiza la evolución mensual del nivel medio global del mar (NOAA) de forma interactiva.")

# ----------------------------
# CARGA DE DATOS
# ----------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/sea_level/sea_level_nasa.csv", skiprows=1, header=None, names=["Fecha", "Nivel_mar"])
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df = df[df["Nivel_mar"] != -999]  # Eliminar valores perdidos
    df = df[df["Nivel_mar"].between(-100, 100)]  # Limpiar valores extremos erróneos como 734 y 104
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    return df

df = cargar_datos()

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.header("🔧 Personaliza la visualización")

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
rango = st.sidebar.slider("Selecciona el rango de años", int(df["Año"].min()), int(df["Año"].max()), (1993, int(df["Año"].max())))
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ----------------------------
# FILTRADO
# ----------------------------
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ----------------------------
# VISUALIZACIÓN PRINCIPAL
# ----------------------------
if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Fecha", y="Nivel_mar", title="Evolución global del nivel del mar",
                  labels={"Nivel_mar": "Nivel del mar (mm)", "Fecha": "Fecha"})
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Fecha", y="Nivel_mar", title="Evolución global del nivel del mar",
                  labels={"Nivel_mar": "Nivel del mar (mm)", "Fecha": "Fecha"})
else:
    fig = px.bar(df_filtrado, x="Fecha", y="Nivel_mar", title="Evolución global del nivel del mar",
                 labels={"Nivel_mar": "Nivel del mar (mm)", "Fecha": "Fecha"})

# Añadir línea de tendencia
if mostrar_tendencia:
    x = df_filtrado["Fecha"].map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    y = df_filtrado["Nivel_mar"].values
    modelo = LinearRegression().fit(x, y)
    y_pred = modelo.predict(x)
    fig.add_scatter(x=df_filtrado["Fecha"], y=y_pred, mode="lines", name="Tendencia",
                    line=dict(color="red", dash="dash", width=2))

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# MÉTRICAS DESTACADAS
# ----------------------------
st.subheader("📌 Indicadores destacados")
nivel_max = df_filtrado["Nivel_mar"].max()
nivel_min = df_filtrado["Nivel_mar"].min()
fecha_max = df_filtrado[df_filtrado["Nivel_mar"] == nivel_max]["Fecha"].dt.strftime("%Y-%m").values[0]
fecha_min = df_filtrado[df_filtrado["Nivel_mar"] == nivel_min]["Fecha"].dt.strftime("%Y-%m").values[0]

st.markdown(f"- 🌊 Máximo nivel registrado: **{nivel_max:.2f} mm** en `{fecha_max}`")
st.markdown(f"- 🌊 Mínimo nivel registrado: **{nivel_min:.2f} mm** en `{fecha_min}`")

if mostrar_tendencia:
    pendiente = modelo.coef_[0] * 365.25  # mm/año
    st.markdown(f"📈 **La tendencia indica un aumento promedio de `{pendiente:.2f} mm/año`.**")

# ----------------------------
# ANÁLISIS POR DÉCADAS
# ----------------------------
if mostrar_decadas:
    st.subheader("📊 Nivel medio del mar por década")
    df_decadas = df_filtrado.copy()
    df_decadas["Década"] = (df_decadas["Año"] // 10) * 10
    df_grouped = df_decadas.groupby("Década")["Nivel_mar"].mean().reset_index()
    st.dataframe(df_grouped.style.format("{:.2f}"))
    fig_dec = px.bar(df_grouped, x="Década", y="Nivel_mar", barmode="group",
                     labels={"Nivel_mar": "Nivel medio (mm)"}, title="Nivel del mar medio por década")
    st.plotly_chart(fig_dec, use_container_width=True)

# ----------------------------
# MODELO PREDICTIVO
# ----------------------------
if mostrar_prediccion:
    st.subheader("🔮 Predicción del nivel del mar hasta 2100")

    x_all = df["Fecha"].map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    y_all = df["Nivel_mar"].values
    modelo = LinearRegression().fit(x_all, y_all)

    fechas_futuras = pd.date_range(start=df["Fecha"].max(), end="2100-12-01", freq="MS")
    x_future = fechas_futuras.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    y_future = modelo.predict(x_future)

    fig_pred = px.line(x=fechas_futuras, y=y_future, labels={"x": "Fecha", "y": "Nivel del mar (mm)"},
                       title="Proyección futura del nivel del mar")
    st.plotly_chart(fig_pred, use_container_width=True)

# ----------------------------
# DESCARGAS
# ----------------------------
st.subheader("💾 Descargar datos o gráfico")

col1, col2 = st.columns(2)

with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="nivel_mar_filtrado.csv", mime="text/csv")

with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer, file_name="grafico_nivel_mar.png", mime="image/png")
