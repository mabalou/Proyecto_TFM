# ==========================================
# 3_Nivel_del_mar.py — versión mejorada (UI/UX)
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

with st.expander("📘 Acerca de esta sección", expanded=True):
    st.markdown("""
    Analiza la evolución mensual del **nivel medio global del mar**, con datos satelitales de la **NOAA / NASA**.

    🔍 **Incluye:**
    - Series temporales interactivas (línea, área o barras).  
    - Cálculo de tendencias lineales y medias por década.  
    - Proyecciones hasta el año 2100 mediante regresión lineal.  
    - Conclusiones automáticas y descarga de resultados.

    ⚙️ Usa la barra lateral para ajustar el rango de años y las opciones de visualización.
    """)

# ------------------------------------------
# CARGA DE DATOS ROBUSTA
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/sea_level/sea_level_nasa.csv", skiprows=1, header=None, names=["Fecha", "Nivel_mar"])
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Nivel_mar"])
    df = df[df["Nivel_mar"].between(-100, 100)]  # eliminar valores extremos
    df = df[df["Nivel_mar"] != -999]  # eliminar códigos de error
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    return df

df = cargar_datos()

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1993, max_year))
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ------------------------------------------
# FILTRADO DE DATOS
# ------------------------------------------
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
st.subheader("📈 Evolución temporal")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
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

    # Línea de tendencia
    if mostrar_tendencia:
        x = df_filtrado["Fecha"].map(pd.Timestamp.toordinal).values.reshape(-1, 1)
        y = df_filtrado["Nivel_mar"].values
        modelo = LinearRegression().fit(x, y)
        y_pred = modelo.predict(x)
        pendiente = modelo.coef_[0] * 365.25  # mm/año
        fig.add_scatter(x=df_filtrado["Fecha"], y=y_pred, mode="lines",
                        name="Tendencia", line=dict(color="red", dash="dash", width=2))

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.markdown("---")
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    nivel_ini = df_filtrado["Nivel_mar"].iloc[0]
    nivel_fin = df_filtrado["Nivel_mar"].iloc[-1]
    cambio = nivel_fin - nivel_ini
    signo = "aumento" if cambio > 0 else "descenso" if cambio < 0 else "estabilidad"

    st.success(
        f"📅 Entre **{rango[0]}** y **{rango[1]}**, se observa un **{signo}** del nivel medio global "
        f"de aproximadamente **{abs(cambio):.2f} mm**.\n\n"
        f"🌊 En {rango[1]}, el nivel medio se sitúa en torno a **{nivel_fin:.2f} mm**, "
        f"frente a **{nivel_ini:.2f} mm** al inicio del periodo."
    )

    if mostrar_tendencia and 'pendiente' in locals():
        st.markdown(f"📈 La tendencia lineal indica un **aumento medio de `{pendiente:.2f} mm/año`**.")
else:
    st.info("Configura un rango de años válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.markdown("---")
    st.subheader("📊 Nivel medio del mar por década")

    df_dec = df_filtrado.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby("Década")["Nivel_mar"].mean().reset_index()

    st.dataframe(df_grouped.style.format({"Nivel_mar": "{:.2f}"}), use_container_width=True)

    fig_dec = px.bar(df_grouped, x="Década", y="Nivel_mar", color="Nivel_mar",
                     color_continuous_scale="Blues",
                     labels={"Nivel_mar": "Nivel medio (mm)"},
                     title="Nivel medio del mar por década")
    st.plotly_chart(fig_dec, use_container_width=True)

    decada_max = int(df_grouped.loc[df_grouped["Nivel_mar"].idxmax(), "Década"])
    valor_max = df_grouped["Nivel_mar"].max()
    st.markdown(f"🌍 La década con mayor nivel medio del mar fue **{decada_max}**, con **{valor_max:.2f} mm**.")

# ------------------------------------------
# MODELO PREDICTIVO
# ------------------------------------------
if mostrar_prediccion and not df.empty:
    st.markdown("---")
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
if not df_filtrado.empty and 'coefg' in locals():
    st.markdown("---")
    st.subheader("🧩 Conclusiones automáticas")

    tendencia = "ascendente" if coefg > 0 else "descendente" if coefg < 0 else "estable"
    frase_tend = (
        "📈 **Aumento sostenido del nivel medio global del mar.**" if coefg > 0 else
        "🟢 **Estabilización o ligera reducción del nivel del mar.**" if coefg < 0 else
        "➖ **Sin cambios significativos observables.**"
    )

    color_fondo = "#ffcccc" if coefg > 0 else "#ccffcc" if coefg < 0 else "#e6e6e6"
    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:#222; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia global es <b>{tendencia}</b>, con una pendiente media de <b>{coefg:.2f} mm/año</b>.</li>
                <li>El cambio neto durante el periodo es de <b>{cambio:.2f} mm</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em;">🔮 Las conclusiones se actualizan automáticamente según el rango seleccionado.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------
# DESCARGAS SEGURAS
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

with col1:
    try:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv,
                           file_name="nivel_mar_filtrado.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                           file_name="grafico_nivel_mar.png", mime="image/png")
    except Exception:
        st.warning("⚠️ Kaleido no disponible — descarga HTML interactivo.")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
