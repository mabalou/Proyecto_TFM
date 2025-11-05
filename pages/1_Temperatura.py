# ==========================================
# 1_Temperatura.py — resumen corregido + conclusiones mejoradas + frase contextual
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="🌡️ Evolución de la Temperatura Global", layout="wide")
st.title("🌍 Evolución de la Temperatura Global")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Esta sección analiza las **anomalías de temperatura global** reportadas por **NASA GISTEMP**.  
    Puedes comparar **estaciones del año**, detectar **tendencias**, explorar **medias por década**
    y generar una **proyección hasta 2100**.
    """)

# -------------------------------
# Carga de datos
# -------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)
    df = df[["Year", "J-D", "DJF", "MAM", "JJA", "SON"]]
    df = df.replace("***", np.nan)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna()

df = cargar_datos()
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
series_disponibles = ["J-D", "DJF", "MAM", "JJA", "SON"]

# -------------------------------
# Estado inicial
# -------------------------------
defaults = {
    "ui_show_filters": False,
    "tipo_grafico": "Línea",
    "rango": (max(1970, min_year), max_year),
    "series_seleccionadas": ["J-D"],
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
    "usar_escala_log": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------------------
# Filtros
# -------------------------------
if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.slider("Selecciona el rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.multiselect("Variables a visualizar", series_disponibles,
                       default=st.session_state.series_seleccionadas, key="series_seleccionadas")
        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")
        st.checkbox("🧮 Escala logarítmica", value=st.session_state.usar_escala_log, key="usar_escala_log")

# -------------------------------
# Parámetros
# -------------------------------
tipo_grafico = st.session_state.tipo_grafico
rango = st.session_state.rango
series = st.session_state.series_seleccionadas
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion
usar_escala_log = st.session_state.usar_escala_log

df_filtrado = df[(df["Year"] >= rango[0]) & (df["Year"] <= rango[1])]

# -------------------------------
# Gráfico y resumen (corrigido)
# -------------------------------
st.subheader("📊 Anomalías globales de temperatura")

if df_filtrado.empty or len(series) == 0:
    st.info("Configura los filtros para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Year", y=series, markers=True,
                          labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"})
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Year", y=series,
                          labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"})
        else:
            fig = px.bar(df_filtrado, x="Year", y=series,
                         labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"})

        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )
        if usar_escala_log:
            fig.update_yaxes(type="log")

        if mostrar_tendencia and len(series) == 1:
            y = df_filtrado[series[0]].values
            x = df_filtrado["Year"].values
            if len(x) > 1:
                coef = np.polyfit(x, y, 1)
                tendencia = coef[0] * x + coef[1]
                fig.add_scatter(x=x, y=tendencia, mode="lines", name="Tendencia",
                                line=dict(color="red", dash="dash", width=2))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_filtrado["Promedio"] = df_filtrado[series].mean(axis=1)
        valor_min = df_filtrado["Promedio"].min()
        valor_max = df_filtrado["Promedio"].max()
        año_min = df_filtrado.loc[df_filtrado["Promedio"].idxmin(), "Year"]
        año_max = df_filtrado.loc[df_filtrado["Promedio"].idxmax(), "Year"]
        media_periodo = df_filtrado["Promedio"].mean()

        st.markdown(f"""
        - 📆 **Años:** {rango[0]}–{rango[1]}  
        - ❄️ **Temperatura mínima:** {valor_min:.3f} °C (*{int(año_min)}*)  
        - 🔥 **Temperatura máxima:** {valor_max:.3f} °C (*{int(año_max)}*)  
        - 🌡️ **Media del período:** {media_periodo:.3f} °C  
        - 📈 **Variables seleccionadas:** {", ".join(series)}
        """)

# -------------------------------
# Media por décadas
# -------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Media de anomalías por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = ((df_dec["Year"] // 10) * 10).astype(int)
    df_dec_group = df_dec.groupby("Década")[series].mean().reset_index()
    fig_dec = px.bar(df_dec_group, x="Década", y=series, barmode="group",
                     labels={"value": "Anomalía media (°C)", "variable": "Variable"})
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# -------------------------------
# Predicción
# -------------------------------
if mostrar_prediccion:
    st.subheader("🔮 Proyección hasta 2100")
    if len(series) == 1:
        serie = series[0]
        df_pred = df[["Year", serie]].dropna()
        titulo = f"Predicción futura ({serie})"
    else:
        df_pred = df[["Year"] + series].copy()
        df_pred["Promedio"] = df_pred[series].mean(axis=1)
        df_pred = df_pred[["Year", "Promedio"]]
        serie = "Promedio"
        titulo = "Predicción futura (promedio de series seleccionadas)"
    x, y = df_pred["Year"].values, df_pred[serie].values
    if len(x) > 5:
        coef = np.polyfit(x, y, 2)
        x_pred = np.arange(x.max() + 1, 2101)
        y_pred = np.polyval(coef, x_pred)
        fig_pred = px.line(x=x_pred, y=y_pred,
                           labels={"x": "Año", "y": "Anomalía (°C)"}, title=titulo)
        st.plotly_chart(fig_pred, use_container_width=True)
        if coef[0] > 0:
            st.success("🌡️ **El modelo sugiere un incremento acelerado de la temperatura hacia finales de siglo.**")
        elif coef[0] < 0:
            st.info("🟢 **El modelo predice un enfriamiento gradual en las próximas décadas.**")
        else:
            st.warning("➖ **El modelo muestra estabilidad sin cambios notables.**")

# -------------------------------
# Conclusiones automáticas (mejoradas)
# -------------------------------
st.subheader("🧩 Conclusiones automáticas")

if not df_filtrado.empty:
    df_filtrado["Promedio"] = df_filtrado[series].mean(axis=1)
    x_all, y_all = df_filtrado["Year"].values, df_filtrado["Promedio"].values
    coef = np.polyfit(x_all, y_all, 1)
    pendiente = coef[0]
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    color_box = "#006666" if pendiente > 0 else "#2e8b57" if pendiente < 0 else "#555555"

    texto = f"""
    📅 En el periodo **{rango[0]}–{rango[1]}**, la temperatura global muestra una tendencia **{tendencia}**.  
    Esto implica que el promedio de anomalías térmicas ha {"aumentado" if pendiente > 0 else "disminuido" if pendiente < 0 else "permanecido estable"} en las últimas décadas.  
    🌡️ **Esto respalda la tendencia observada de calentamiento global durante el siglo XX.**
    """

    st.markdown(
        f"<div style='background-color:{color_box};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
        unsafe_allow_html=True
    )

# -------------------------------
# Exportar
# -------------------------------
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="temperatura_filtrada.csv", mime="text/csv")
with col2:
    import plotly.io as pio
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name="grafico_temperatura.png", mime="image/png")
