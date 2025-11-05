# ==========================================
# 4_Hielo_marino.py — versión sincronizada con header
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
st.set_page_config(page_title="🧊 Hielo marino", layout="wide")
st.title("🧊 Evolución del hielo marino global")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la evolución de la **extensión del hielo marino** en el **Ártico** y el **Antártico** (1978–presente).

    🔍 **Incluye:**
    - Series interactivas (línea, área o barras).  
    - Cálculo de tendencias lineales.  
    - Promedios por décadas.  
    - Comparativa entre regiones y conclusiones automáticas.  
    - Descarga de datos y gráficos.  
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos(region):
    archivo = "data/hielo/arctic_sea_ice_extent.csv" if region == "Ártico" else "data/hielo/antarctic_sea_ice_extent.csv"
    df = pd.read_csv(archivo)
    df.columns = df.columns.str.strip()
    columnas_esperadas = {"Year", "Month", "Extent"}
    if not columnas_esperadas.issubset(df.columns):
        raise ValueError(f"El archivo {archivo} no contiene las columnas esperadas. Detectadas: {list(df.columns)}")
    df = df[["Year", "Month", "Extent"]].dropna()
    df = df.rename(columns={"Year": "Año", "Month": "Mes", "Extent": "Extensión"})
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
    df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce")
    df["Extensión"] = pd.to_numeric(df["Extensión"], errors="coerce")
    df = df.dropna()
    df_anual = df.groupby("Año")["Extensión"].mean().reset_index()
    return df_anual

@st.cache_data
def cargar_datos_ambos():
    artico = cargar_datos("Ártico").copy()
    artico["Región"] = "Ártico"
    antartico = cargar_datos("Antártico").copy()
    antartico["Región"] = "Antártico"
    return pd.concat([artico, antartico], ignore_index=True)

# ------------------------------------------
# ESTADO Y FILTROS (sin sidebar)
# ------------------------------------------
defaults = {
    "ui_show_filters": False,
    "region": "Ártico",
    "tipo_grafico": "Línea",
    "rango": (1980, 2024),
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "comparar_regiones": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.selectbox("🌍 Región", ["Ártico", "Antártico"], key="region")
        st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.slider("Rango de años", 1978, 2024, st.session_state.rango, key="rango")
        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🌐 Comparar ambas regiones", value=st.session_state.comparar_regiones, key="comparar_regiones")

region = st.session_state.region
tipo_grafico = st.session_state.tipo_grafico
rango = st.session_state.rango
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
comparar_regiones = st.session_state.comparar_regiones

# ------------------------------------------
# CARGA Y FILTRADO
# ------------------------------------------
df = cargar_datos(region)
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
st.subheader("📈 Evolución temporal")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
    titulo = f"Evolución de la extensión del hielo marino ({region})"
    if tipo_grafico == "Línea":
        fig = px.line(df_filtrado, x="Año", y="Extensión", markers=True,
                      labels={"Extensión": "Extensión (millones km²)", "Año": "Año"},
                      title=titulo)
    elif tipo_grafico == "Área":
        fig = px.area(df_filtrado, x="Año", y="Extensión",
                      labels={"Extensión": "Extensión (millones km²)", "Año": "Año"},
                      title=titulo)
    else:
        fig = px.bar(df_filtrado, x="Año", y="Extensión",
                     labels={"Extensión": "Extensión (millones km²)", "Año": "Año"},
                     title=titulo)

    if mostrar_tendencia:
        x = df_filtrado["Año"].values.reshape(-1, 1)
        y = df_filtrado["Extensión"].values
        modelo = LinearRegression().fit(x, y)
        y_pred = modelo.predict(x)
        coef = modelo.coef_[0]
        fig.add_scatter(x=df_filtrado["Año"], y=y_pred, mode="lines", name="Tendencia",
                        line=dict(color="red", dash="dash", width=2))
        st.markdown(f"📉 La tendencia indica un cambio medio de `{coef:.4f}` millones km²/año.")

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    inicio, fin = df_filtrado["Extensión"].iloc[0], df_filtrado["Extensión"].iloc[-1]
    cambio = fin - inicio
    signo = "disminución" if cambio < 0 else "aumento" if cambio > 0 else "estabilidad"

    st.success(
        f"📅 Entre **{rango[0]}** y **{rango[1]}**, se observa una **{signo}** "
        f"de aproximadamente **{abs(cambio):.2f} millones km²** en la extensión del hielo marino del **{region}**."
    )
else:
    st.info("Selecciona un rango válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.markdown("---")
    with st.expander("📊 Media de extensión por década", expanded=True):
        df_decada = df_filtrado.copy()
        df_decada["Década"] = (df_decada["Año"] // 10) * 10
        df_grouped = df_decada.groupby("Década")["Extensión"].mean().reset_index()

        st.dataframe(df_grouped.style.format({"Extensión": "{:.2f}"}), use_container_width=True)
        fig_dec = px.bar(df_grouped, x="Década", y="Extensión", color="Extensión",
                         color_continuous_scale="Blues",
                         labels={"Extensión": "Extensión promedio (millones km²)"},
                         title=f"Media por década ({region})")
        st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# COMPARATIVA ENTRE REGIONES
# ------------------------------------------
if comparar_regiones:
    st.markdown("---")
    with st.expander("🌐 Comparativa entre regiones polares", expanded=True):
        df_comp = cargar_datos_ambos()
        df_comp = df_comp[(df_comp["Año"] >= rango[0]) & (df_comp["Año"] <= rango[1])]

        fig_comp = px.line(df_comp, x="Año", y="Extensión", color="Región",
                           title="Comparativa de extensión del hielo marino (Ártico vs Antártico)",
                           labels={"Extensión": "Extensión (millones km²)", "Año": "Año"})
        st.plotly_chart(fig_comp, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
if not df_filtrado.empty and mostrar_tendencia:
    st.markdown("---")
    st.subheader("🧩 Conclusiones automáticas")

    tendencia = "descendente" if coef < 0 else "ascendente" if coef > 0 else "estable"
    frase_tend = (
        "📉 **Disminución constante de la extensión del hielo marino.**" if coef < 0 else
        "📈 **Aumento gradual de la extensión del hielo marino.**" if coef > 0 else
        "➖ **Sin cambios significativos detectables.**"
    )

    color_fondo = "#ffcccc" if coef < 0 else "#ccffcc" if coef > 0 else "#e6e6e6"
    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:#222; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia general en el <b>{region}</b> es <b>{tendencia}</b> ({coef:.4f} millones km²/año).</li>
                <li>El cambio total observado es de <b>{cambio:.2f} millones km²</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em;">🔮 Estas conclusiones se actualizan automáticamente según la región y rango seleccionados.</p>
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
                           file_name=f"hielo_marino_{region.lower()}.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                           file_name=f"grafico_hielo_{region.lower()}.png", mime="image/png")
    except Exception:
        st.warning("⚠️ Kaleido no disponible — descarga HTML interactivo.")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
