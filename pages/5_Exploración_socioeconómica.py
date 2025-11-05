# ==========================================
# 5_Exploración_socioeconómica.py — versión con resumen lateral + ejes ampliados + conclusiones automáticas
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="📊 Exploración Socioeconómica", layout="wide")
st.title("📉 Evolución de las Emisiones de CO₂ por País")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la **evolución histórica de las emisiones de CO₂** por país a lo largo del tiempo.  

    🔍 **Incluye:**
    - Visualizaciones interactivas (línea, área o barras).  
    - Tendencias lineales automáticas.  
    - Promedios por décadas y comparativas globales.  
    - Predicciones futuras hasta el año 2100.  
    - Descarga directa de datos y gráficos.  
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/socioeconomico/co2_emissions_by_country.csv")
    df.columns = df.columns.str.strip().str.lower()

    year_col = next((c for c in df.columns if "year" in c), None)
    country_col = next((c for c in df.columns if "country" in c), None)
    emission_col = next((c for c in df.columns if "co2" in c or "emission" in c), None)

    if not all([year_col, country_col, emission_col]):
        st.error(f"No se encontraron columnas esperadas en el CSV.\n\nColumnas detectadas: {list(df.columns)}")
        st.stop()

    df = df.rename(columns={
        year_col: "Year",
        country_col: "Country",
        emission_col: "CO2_Emissions_Mt"
    })

    df = df[["Year", "Country", "CO2_Emissions_Mt"]].dropna()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["CO2_Emissions_Mt"] = pd.to_numeric(df["CO2_Emissions_Mt"], errors="coerce")
    return df

df = cargar_datos()
paises = sorted(df["Country"].unique())
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())

# ------------------------------------------
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
    "ui_show_filters": False,
    "paises_seleccionados": ["Spain", "United States"],
    "rango": (1980, max_year),
    "tipo_grafico": "Línea",
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
    "usar_escala_log": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.multiselect("🌍 Selecciona países", paises, key="paises_seleccionados")
        st.slider("📆 Rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.selectbox("📊 Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")
        st.checkbox("🧮 Escala logarítmica", value=st.session_state.usar_escala_log, key="usar_escala_log")

paises_seleccionados = st.session_state.paises_seleccionados
rango = st.session_state.rango
tipo_grafico = st.session_state.tipo_grafico
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion
usar_escala_log = st.session_state.usar_escala_log

# ------------------------------------------
# FILTRADO DE DATOS
# ------------------------------------------
df_filtrado = df[(df["Country"].isin(paises_seleccionados)) & (df["Year"].between(*rango))]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL + RESUMEN LATERAL
# ------------------------------------------
st.subheader("📈 Evolución histórica")

if df_filtrado.empty:
    st.info("Selecciona al menos un país y un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Year", y="CO2_Emissions_Mt", color="Country", markers=True,
                          labels={"CO2_Emissions_Mt": "Emisiones (Mt CO₂)", "Country": "País", "Year": "Año"},
                          title="Evolución de las emisiones de CO₂")
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Year", y="CO2_Emissions_Mt", color="Country",
                          labels={"CO2_Emissions_Mt": "Emisiones (Mt CO₂)", "Country": "País", "Year": "Año"},
                          title="Evolución de las emisiones de CO₂")
        else:
            fig = px.bar(df_filtrado, x="Year", y="CO2_Emissions_Mt", color="Country",
                         labels={"CO2_Emissions_Mt": "Emisiones (Mt CO₂)", "Country": "País", "Year": "Año"},
                         title="Evolución de las emisiones de CO₂")

        # Ejes más grandes
        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )

        if usar_escala_log:
            fig.update_yaxes(type="log")

        if mostrar_tendencia and len(paises_seleccionados) == 1:
            pais = paises_seleccionados[0]
            df_pais = df_filtrado[df_filtrado["Country"] == pais]
            x, y = df_pais["Year"].values, df_pais["CO2_Emissions_Mt"].values
            if len(x) > 1:
                coef = np.polyfit(x, y, 1)
                y_pred = np.polyval(coef, x)
                fig.add_scatter(x=x, y=y_pred, mode="lines", name="Tendencia",
                                line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_mean = df_filtrado.groupby("Country")["CO2_Emissions_Mt"].mean().sort_values(ascending=False)
        top_pais, top_val = df_mean.idxmax(), df_mean.max()
        min_pais, min_val = df_mean.idxmin(), df_mean.min()

        df_global = df_filtrado.groupby("Year")["CO2_Emissions_Mt"].mean().reset_index()
        pendiente_global = np.polyfit(df_global["Year"], df_global["CO2_Emissions_Mt"], 1)[0] if len(df_global) > 5 else 0

        st.markdown(f"""
        - 🌍 **País con más emisiones:** {top_pais} ({top_val:.2f} Mt CO₂/año)  
        - 🌱 **País con menos emisiones:** {min_pais} ({min_val:.2f} Mt CO₂/año)  
        - 📈 **Tendencia global:** {'Ascendente' if pendiente_global > 0 else 'Descendente' if pendiente_global < 0 else 'Estable'}  
        - 📆 **Periodo:** {rango[0]}–{rango[1]}  
        """)

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Media de emisiones por década")
    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Year"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby(["Década", "Country"])["CO2_Emissions_Mt"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="CO2_Emissions_Mt", color="Country",
                     labels={"CO2_Emissions_Mt": "Emisiones promedio (Mt CO₂)", "Country": "País"},
                     barmode="group", title="Emisiones promedio por década")
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# MODELO PREDICTIVO
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    st.subheader("🔮 Predicción de emisiones hasta 2100")
    if len(paises_seleccionados) == 1:
        df_pred = df[df["Country"] == paises_seleccionados[0]]
        serie = paises_seleccionados[0]
    else:
        df_pred = df[df["Country"].isin(paises_seleccionados)].groupby("Year")["CO2_Emissions_Mt"].mean().reset_index()
        serie = "Promedio Global"

    x, y = df_pred["Year"].values, df_pred["CO2_Emissions_Mt"].values
    if len(x) > 5:
        coef = np.polyfit(x, y, 2)
        x_pred = np.arange(x.max() + 1, 2101)
        y_pred = np.polyval(coef, x_pred)
        fig_pred = px.line(x=x_pred, y=y_pred,
                           labels={"x": "Año", "y": "Emisiones (Mt CO₂)"},
                           title=f"Proyección futura ({serie}) hasta 2100")
        st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")

if not df_filtrado.empty:
    pendiente = pendiente_global if "pendiente_global" in locals() else 0
    color_box = "#006666" if pendiente > 0 else "#2e8b57" if pendiente < 0 else "#555555"
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"

    texto = f"""
    📅 Entre **{rango[0]}** y **{rango[1]}**, las emisiones globales de CO₂ muestran una tendencia **{tendencia}**.  
    Esto refleja una **{'subida continuada en los países industrializados' if pendiente > 0 else 'ligera mejora en la reducción de emisiones' if pendiente < 0 else 'situación estable sin cambios notables'}**.  
    🔬 **Estos resultados se alinean con los informes internacionales del IPCC.**
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
    st.download_button("📄 Descargar CSV", data=csv,
                       file_name="co2_emisiones_filtradas.csv", mime="text/csv")

with col2:
    import plotly.io as pio
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                       file_name="grafico_co2.png", mime="image/png")
