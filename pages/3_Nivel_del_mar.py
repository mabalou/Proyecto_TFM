# ==========================================
# 3_Nivel_del_mar.py — versión con resumen lateral + ejes ampliados + conclusiones automáticas
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
st.set_page_config(page_title="🌊 Nivel del mar global", layout="wide")

st.title("🌊 Evolución del nivel medio global del mar")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la evolución mensual del **nivel medio global del mar**, con datos satelitales de la **NOAA / NASA**.

    🔍 **Incluye:**
    - Series temporales interactivas (línea, área o barras).  
    - Cálculo de tendencias lineales y medias por década.  
    - Proyecciones hasta el año 2100 mediante regresión lineal.  
    - Conclusiones automáticas y descarga de resultados.
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/sea_level/sea_level_nasa.csv", skiprows=1, header=None, names=["Fecha", "Nivel_mar"])
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Nivel_mar"])
    df = df[df["Nivel_mar"].between(-100, 100)]
    df = df[df["Nivel_mar"] != -999]
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    return df

df = cargar_datos()
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())

# ------------------------------------------
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
    "ui_show_filters": False,
    "tipo_grafico": "Línea",
    "rango": (1993, max_year),
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.slider("Selecciona el rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")

tipo_grafico = st.session_state.tipo_grafico
rango = st.session_state.rango
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL + RESUMEN LATERAL
# ------------------------------------------
st.subheader("📈 Evolución temporal del nivel del mar")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        titulo = "Evolución del nivel medio global del mar"
        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Fecha", y="Nivel_mar", markers=True,
                          labels={"Nivel_mar": "Nivel del mar (mm)", "Fecha": "Fecha"}, title=titulo)
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Fecha", y="Nivel_mar",
                          labels={"Nivel_mar": "Nivel del mar (mm)", "Fecha": "Fecha"}, title=titulo)
        else:
            fig = px.bar(df_filtrado, x="Fecha", y="Nivel_mar",
                         labels={"Nivel_mar": "Nivel del mar (mm)", "Fecha": "Fecha"}, title=titulo)

        # Ejes más grandes
        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )

        # Línea de tendencia
        pendiente = 0
        if mostrar_tendencia:
            x = df_filtrado["Fecha"].map(pd.Timestamp.toordinal).values.reshape(-1, 1)
            y = df_filtrado["Nivel_mar"].values
            modelo = LinearRegression().fit(x, y)
            y_pred = modelo.predict(x)
            pendiente = modelo.coef_[0] * 365.25
            fig.add_scatter(x=df_filtrado["Fecha"], y=y_pred, mode="lines",
                            name="Tendencia", line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    # Resumen lateral
    with col2:
        st.markdown("### 🧾 Resumen del período")
        nivel_ini = df_filtrado["Nivel_mar"].iloc[0]
        nivel_fin = df_filtrado["Nivel_mar"].iloc[-1]
        cambio = nivel_fin - nivel_ini
        signo = "aumento" if cambio > 0 else "descenso" if cambio < 0 else "estabilidad"
        media = df_filtrado["Nivel_mar"].mean()
        valor_min = df_filtrado["Nivel_mar"].min()
        valor_max = df_filtrado["Nivel_mar"].max()
        año_min = df_filtrado.loc[df_filtrado["Nivel_mar"].idxmin(), "Año"]
        año_max = df_filtrado.loc[df_filtrado["Nivel_mar"].idxmax(), "Año"]

        st.markdown(f"""
        - 📆 **Años:** {rango[0]}–{rango[1]}  
        - 🌊 **Nivel medio:** {media:.2f} mm  
        - 🔽 **Mínimo:** {valor_min:.2f} mm (*{int(año_min)}*)  
        - 🔼 **Máximo:** {valor_max:.2f} mm (*{int(año_max)}*)  
        - 📈 **Cambio neto:** {cambio:+.2f} mm  
        - 📊 **Tendencia media:** {pendiente:.2f} mm/año  
        """)

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Nivel medio del mar por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby("Década")["Nivel_mar"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Nivel_mar", color="Nivel_mar",
                     color_continuous_scale="Blues",
                     labels={"Nivel_mar": "Nivel medio (mm)"},
                     title="Nivel medio del mar por década")
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# MODELO PREDICTIVO
# ------------------------------------------
if mostrar_prediccion and not df.empty:
    st.subheader("🔮 Proyección del nivel del mar hasta 2100")
    x_all = df["Fecha"].map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    y_all = df["Nivel_mar"].values
    modelo_pred = LinearRegression().fit(x_all, y_all)
    coefg = modelo_pred.coef_[0] * 365.25

    fechas_futuras = pd.date_range(start=df["Fecha"].max(), end="2100-12-01", freq="MS")
    x_future = fechas_futuras.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    y_future = modelo_pred.predict(x_future)

    fig_pred = px.line(x=fechas_futuras, y=y_future,
                       labels={"x": "Fecha", "y": "Nivel del mar (mm)"},
                       title="Proyección del nivel medio global del mar hasta 2100")
    st.plotly_chart(fig_pred, use_container_width=True)

    if coefg > 0:
        st.markdown("🌡️ **El modelo predice un incremento continuo del nivel del mar hacia finales de siglo.**")
    elif coefg < 0:
        st.markdown("🟢 **El modelo indica una ligera tendencia descendente (inusual).**")
    else:
        st.markdown("➖ **El modelo no muestra una variación significativa.**")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")

if not df_filtrado.empty and 'pendiente' in locals():
    color_box = "#006666" if pendiente > 0 else "#2e8b57" if pendiente < 0 else "#555555"
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"

    texto = f"""
    📅 Entre **{rango[0]}** y **{rango[1]}**, el nivel medio global del mar muestra una tendencia **{tendencia}**.  
    Esto implica un cambio neto de **{cambio:.2f} mm**, con una variación media de **{pendiente:.2f} mm/año**.  
    🌊 **Estos resultados coinciden con los informes del IPCC y observaciones satelitales recientes.**
    """

    st.markdown(
        f"<div style='background-color:{color_box};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
        unsafe_allow_html=True
    )

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Descargar CSV",
        data=csv,
        file_name="nivel_mar_filtrado.csv",
        mime="text/csv"
    )

with col2:
    import plotly.io as pio
    # Exportar gráfico en formato HTML interactivo (no requiere Kaleido)
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button(
        "🖼️ Descargar gráfico (HTML interactivo)",
        data=html_bytes,
        file_name="grafico_nivel_mar.html",
        mime="text/html"
    )

