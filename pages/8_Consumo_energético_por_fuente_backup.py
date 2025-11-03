# ==========================================
# 8_Consumo_energético_por_fuente.py (versión mejorada visual)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="⚡ Consumo Energético por Fuente", layout="wide")

# TÍTULO Y DESCRIPCIÓN
st.title("⚡ Evolución del consumo energético global")

with st.expander("📘 Descripción general", expanded=True):
    st.markdown("""
    Analiza la evolución del **consumo mundial de energía por fuente**
    (carbón, petróleo, gas, renovables, nuclear, hidroeléctrica, etc.).

    Esta visualización permite:
    - Comparar fuentes energéticas por año o década.  
    - Aplicar **escalas logarítmicas**.  
    - Añadir líneas de tendencia y proyecciones hasta 2100.  
    - Exportar datos y gráficos en distintos formatos.
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/energia/energy_consuption_by_source.csv")
    df.columns = df.columns.str.strip().str.lower()
    df = df.groupby("year").sum(numeric_only=True).reset_index()
    df = df.rename(columns={"year": "Año"})
    largo = df.melt(id_vars="Año", var_name="Fuente", value_name="Consumo")
    largo = largo.dropna(subset=["Consumo"])
    return largo

df = cargar_datos()

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza tu análisis")

fuentes = sorted(df["Fuente"].unique())
fuentes_sel = st.sidebar.multiselect(
    "Selecciona fuentes energéticas:",
    opciones := fuentes,
    default=fuentes[:5]
)
rango = st.sidebar.slider("Rango de años", 1960, int(df["Año"].max()), (1980, int(df["Año"].max())))
tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área (apilada)", "Barras"])
usar_log = st.sidebar.checkbox("Escala logarítmica")
mostrar_prediccion = st.sidebar.checkbox("🔮 Añadir proyección hasta 2100", value=True)

# ------------------------------------------
# FILTRADO
# ------------------------------------------
df_filtrado = df[df["Fuente"].isin(fuentes_sel) & df["Año"].between(*rango)]

# ------------------------------------------
# VISUALIZACIÓN
# ------------------------------------------
st.subheader("📊 Evolución por fuente")

if df_filtrado.empty:
    st.warning("No hay datos en el rango seleccionado.")
else:
    if tipo_grafico == "Línea":
        fig = px.line(df_filtrado, x="Año", y="Consumo", color="Fuente", markers=True)
    elif tipo_grafico == "Área (apilada)":
        fig = px.area(df_filtrado, x="Año", y="Consumo", color="Fuente")
    else:
        fig = px.bar(df_filtrado, x="Año", y="Consumo", color="Fuente")

    if usar_log:
        fig.update_yaxes(type="log", title="Consumo energético (log)")

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN LINEAL SIMPLE
# ------------------------------------------
if mostrar_prediccion:
    st.subheader("🔮 Proyección hasta 2100")

    fig_pred = px.line(labels={"x": "Año", "y": "Consumo (TWh)"})
    for fuente in fuentes_sel:
        datos = df[df["Fuente"] == fuente]
        if len(datos) > 1:
            X = datos["Año"].values.reshape(-1, 1)
            y = datos["Consumo"].values
            modelo = LinearRegression().fit(X, y)
            años_futuros = np.arange(X.max() + 1, 2101).reshape(-1, 1)
            pred = modelo.predict(años_futuros)
            fig_pred.add_scatter(x=años_futuros.flatten(), y=pred, mode="lines", name=f"{fuente} (proyección)")

    st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# EXPORTACIÓN DE DATOS Y GRÁFICOS
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)

with col1:
    if not df_filtrado.empty:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv, file_name="consumo_energetico.csv", mime="text/csv")

with col2:
    try:
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name="grafico_consumo.png", mime="image/png")
    except Exception:
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)", data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
