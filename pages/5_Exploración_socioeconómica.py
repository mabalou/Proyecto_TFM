# ==========================================
# 5_Exploración_socioeconómica.py — versión mejorada (UI/UX)
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

with st.expander("📘 Acerca de esta sección", expanded=True):
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
# CARGA ROBUSTA DE DATOS
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

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

paises = sorted(df["Country"].unique())
paises_seleccionados = st.sidebar.multiselect("🌍 Selecciona países", paises, default=["Spain", "United States"])

min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
rango = st.sidebar.slider("📆 Rango de años", min_year, max_year, (1980, max_year))

tipo_grafico = st.sidebar.selectbox("📊 Tipo de gráfico", ["Línea", "Área", "Barras"])
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)
usar_escala_log = st.sidebar.checkbox("🧮 Escala logarítmica", value=False)

# ------------------------------------------
# FILTRADO DE DATOS
# ------------------------------------------
df_filtrado = df[(df["Country"].isin(paises_seleccionados)) & (df["Year"].between(*rango))]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
st.subheader("📈 Evolución histórica")

if df_filtrado.empty:
    st.info("Selecciona al menos un país y un rango de años válido para visualizar los datos.")
else:
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

    if usar_escala_log:
        fig.update_yaxes(type="log")

    # Tendencia solo si un país
    if mostrar_tendencia and len(paises_seleccionados) == 1:
        pais = paises_seleccionados[0]
        df_pais = df_filtrado[df_filtrado["Country"] == pais]
        x, y = df_pais["Year"].values, df_pais["CO2_Emissions_Mt"].values
        if len(x) > 1:
            coef = np.polyfit(x, y, 1)
            y_pred = np.polyval(coef, x)
            fig.add_scatter(x=x, y=y_pred, mode="lines", name="Tendencia",
                            line=dict(color="red", dash="dash"))
            st.caption(f"📉 Pendiente media en {pais}: `{coef[0]:.2f}` Mt CO₂/año")

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.markdown("---")
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    df_mean = df_filtrado.groupby("Country")["CO2_Emissions_Mt"].mean().sort_values(ascending=False)
    top_pais, top_val = df_mean.idxmax(), df_mean.max()
    min_pais, min_val = df_mean.idxmin(), df_mean.min()

    resumen = (
        f"🌍 Durante el periodo **{rango[0]}–{rango[1]}**, el país con mayores emisiones promedio fue **{top_pais}** "
        f"con aproximadamente **{top_val:.2f} Mt CO₂/año**.\n\n"
        f"🌱 El país con menores emisiones promedio fue **{min_pais}**, con **{min_val:.2f} Mt CO₂/año**."
    )

    # Tendencia global
    df_global = df_filtrado.groupby("Year")["CO2_Emissions_Mt"].mean().reset_index()
    if len(df_global) > 5:
        coefg = np.polyfit(df_global["Year"], df_global["CO2_Emissions_Mt"], 1)
        pendiente_global = coefg[0]
        if pendiente_global > 0:
            resumen += "\n\n📈 Las emisiones globales muestran una **tendencia ascendente sostenida**."
        elif pendiente_global < 0:
            resumen += "\n\n🟢 Se observa una **reducción o estabilización** en las emisiones promedio."
        else:
            resumen += "\n\n➖ Las emisiones se han mantenido **relativamente estables**."

    st.success(resumen)
else:
    st.info("Selecciona al menos un país y un rango válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.markdown("---")
    st.subheader("📊 Media de emisiones por década")

    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Year"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby(["Década", "Country"])["CO2_Emissions_Mt"].mean().reset_index()

    st.dataframe(df_grouped.style.format({"CO2_Emissions_Mt": "{:.2f}"}), use_container_width=True)

    fig_dec = px.bar(df_grouped, x="Década", y="CO2_Emissions_Mt", color="Country",
                     labels={"CO2_Emissions_Mt": "Emisiones promedio (Mt CO₂)", "Country": "País"},
                     barmode="group", title="Emisiones promedio por década")
    st.plotly_chart(fig_dec, use_container_width=True)

    df_prom = df_grouped.groupby("Década")["CO2_Emissions_Mt"].mean()
    decada_max, valor_max = df_prom.idxmax(), df_prom.max()
    st.markdown(f"📅 La década con mayores emisiones promedio fue la de **{int(decada_max)}**, con **{valor_max:.2f} Mt CO₂**.")

# ------------------------------------------
# MODELO PREDICTIVO
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    st.markdown("---")
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

        if coef[0] > 0:
            st.markdown("🌡️ **El modelo sugiere un incremento acelerado de las emisiones hacia finales de siglo.**")
        elif coef[0] < 0:
            st.markdown("🟢 **El modelo predice una disminución gradual en las próximas décadas.**")
        else:
            st.markdown("➖ **El modelo muestra estabilidad sin variaciones significativas.**")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
if not df_filtrado.empty and 'coefg' in locals():
    st.markdown("---")
    st.subheader("🧩 Conclusiones automáticas")

    pendiente = coefg[0] if isinstance(coefg, (list, np.ndarray)) else coefg
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    frase_tend = (
        "📈 **Aumento sostenido de las emisiones de CO₂.**" if pendiente > 0 else
        "🟢 **Reducción o estabilización en las emisiones globales.**" if pendiente < 0 else
        "➖ **Sin cambios relevantes en las emisiones.**"
    )

    color_fondo = "#ffcccc" if pendiente > 0 else "#ccffcc" if pendiente < 0 else "#e6e6e6"
    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:#222; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia global de emisiones es <b>{tendencia}</b>.</li>
                <li>La década más emisora fue la de <b>{int(decada_max)}</b> con <b>{valor_max:.2f} Mt CO₂</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em;">🔮 Estas conclusiones se actualizan automáticamente al modificar el rango o los países seleccionados.</p>
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
                           file_name="co2_emisiones_filtradas.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                           file_name="grafico_co2.png", mime="image/png")
    except Exception:
        st.warning("⚠️ Kaleido no disponible — descarga HTML interactivo.")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
