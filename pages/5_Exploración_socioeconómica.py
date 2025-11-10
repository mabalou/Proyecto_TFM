# ==========================================
# 5_Exploración_socioeconómica.py — versión mejorada (funcional, sin KeyError)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="📊 Exploración Socioeconómica", layout="wide")
st.title("📉 Evolución de las Emisiones de CO₂ por País")

# ------------------------------------------
# EXPLICACIÓN
# ------------------------------------------
with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la **evolución histórica de las emisiones de CO₂** por país.  

    🔍 **Incluye:**
    - Visualizaciones interactivas con **suavizado**.  
    - Cálculo de **tendencias lineales** y **promedios por década**.  
    - **Predicciones hasta 2100** con **intervalo de confianza del 95 %**.  
    - Descarga de datos y gráficos interactivos.
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

paises_sel = st.session_state.paises_seleccionados
rango = st.session_state.rango
tipo_grafico = st.session_state.tipo_grafico
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion
usar_escala_log = st.session_state.usar_escala_log

# ------------------------------------------
# FILTRADO + SUAVIZADO
# ------------------------------------------
df_filtrado = df[(df["Country"].isin(paises_sel)) & (df["Year"].between(*rango))].copy()
df_filtrado["Smoothed"] = df_filtrado.groupby("Country")["CO2_Emissions_Mt"].transform(
    lambda x: x.rolling(window=3, center=True, min_periods=1).mean()
)

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL + RESUMEN
# ------------------------------------------
st.subheader("📈 Evolución histórica de las emisiones de CO₂")

if df_filtrado.empty:
    st.info("Selecciona al menos un país y un rango de años válido.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    # --- Gráfico principal ---
    with col1:
        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Year", y="Smoothed", color="Country", markers=True,
                          labels={"Smoothed": "Emisiones (Mt CO₂)", "Year": "Año", "Country": "País"},
                          title="Evolución de las emisiones (suavizada)")
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Year", y="Smoothed", color="Country",
                          labels={"Smoothed": "Emisiones (Mt CO₂)", "Year": "Año", "Country": "País"})
        else:
            fig = px.bar(df_filtrado, x="Year", y="Smoothed", color="Country",
                         labels={"Smoothed": "Emisiones (Mt CO₂)", "Year": "Año", "Country": "País"})

        if usar_escala_log:
            fig.update_yaxes(type="log")

        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15),
            legend_title_text="País"
        )

        pendiente = 0
        if mostrar_tendencia and len(paises_sel) == 1:
            pais = paises_sel[0]
            df_p = df_filtrado[df_filtrado["Country"] == pais]
            X, Y = df_p["Year"].values.reshape(-1, 1), df_p["Smoothed"].values
            modelo = LinearRegression().fit(X, Y)
            Y_pred = modelo.predict(X)
            pendiente = modelo.coef_[0]
            fig.add_scatter(x=df_p["Year"], y=Y_pred, mode="lines",
                            name="Tendencia", line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    # --- Resumen lateral ---
    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_mean = df_filtrado.groupby("Country")["Smoothed"].mean().sort_values(ascending=False)
        top_pais, top_val = df_mean.idxmax(), df_mean.max()
        min_pais, min_val = df_mean.idxmin(), df_mean.min()

        df_global = df_filtrado.groupby("Year")["Smoothed"].mean().reset_index()
        pendiente_global = np.polyfit(df_global["Year"], df_global["Smoothed"], 1)[0] if len(df_global) > 5 else 0

        st.markdown(f"""
        - 🌍 **País con más emisiones:** {top_pais} ({top_val:.2f} Mt CO₂/año)  
        - 🌱 **País con menos emisiones:** {min_pais} ({min_val:.2f} Mt CO₂/año)  
        - 📈 **Tendencia global:** {'Ascendente' if pendiente_global > 0 else 'Descendente' if pendiente_global < 0 else 'Estable'}  
        - 📆 **Periodo:** {rango[0]}–{rango[1]}  
        """)

        st.markdown("### ⚙️ Ajustar visualización")
        st.multiselect("🌍 Selecciona países", paises, default=paises_sel, key="paises_seleccionados")
        st.slider("📆 Rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.selectbox("📊 Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.checkbox("📈 Mostrar tendencia", value=mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Media por décadas", value=mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=mostrar_prediccion, key="mostrar_prediccion")

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Emisiones promedio por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = ((df_dec["Year"] // 10) * 10).astype(int)
    df_dec = df_dec.groupby(["Década", "Country"])["Smoothed"].mean().reset_index()
    fig_dec = px.bar(df_dec, x="Década", y="Smoothed", color="Country",
                     labels={"Smoothed": "Emisiones promedio (Mt CO₂)", "Country": "País"},
                     barmode="group", title="Media de emisiones por década")
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# MODELO PREDICTIVO CON INTERVALO 95 %
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    st.subheader("🔮 Predicción de emisiones hasta 2100")
    if len(paises_sel) == 1:
        df_pred = df[df["Country"] == paises_sel[0]]
        serie = paises_sel[0]
    else:
        df_pred = df[df["Country"].isin(paises_sel)].groupby("Year")["CO2_Emissions_Mt"].mean().reset_index()
        serie = "Promedio Global"

    X = df_pred["Year"].values.reshape(-1, 1)
    Y = df_pred["CO2_Emissions_Mt"].values
    modelo = LinearRegression().fit(X, Y)
    future = np.arange(df_pred["Year"].max() + 1, 2101).reshape(-1, 1)
    y_pred = modelo.predict(future)

    resid = Y - modelo.predict(X)
    s = np.std(resid)
    y_upper = y_pred + 1.96 * s
    y_lower = y_pred - 1.96 * s

    fig_pred = px.line(x=future.ravel(), y=y_pred,
                       labels={"x": "Año", "y": "Emisiones (Mt CO₂)"},
                       title=f"Predicción de emisiones — {serie}")
    fig_pred.add_scatter(x=future.ravel(), y=y_upper, mode="lines",
                         line=dict(color="cyan", width=1), name="IC 95 % (sup.)")
    fig_pred.add_scatter(x=future.ravel(), y=y_lower, mode="lines",
                         fill="tonexty", fillcolor="rgba(0,191,255,0.2)",
                         line=dict(color="cyan", width=1), name="IC 95 % (inf.)")
    st.plotly_chart(fig_pred, use_container_width=True)

    if modelo.coef_[0] > 0:
        st.success("🌡️ El modelo predice un incremento sostenido de las emisiones hacia 2100 (IC 95 %).")
    elif modelo.coef_[0] < 0:
        st.info("🟢 El modelo sugiere una tendencia descendente sostenida (IC 95 %).")
    else:
        st.warning("➖ No se observan variaciones significativas en la proyección (IC 95 %).")

# ------------------------------------------
# CONCLUSIONES
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")
if not df_filtrado.empty:
    pendiente = pendiente_global if "pendiente_global" in locals() else 0
    color = "#006666" if pendiente > 0 else "#2e8b57" if pendiente < 0 else "#555555"
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    texto = f"""
    📅 Entre **{rango[0]}** y **{rango[1]}**, las emisiones globales muestran una tendencia **{tendencia}**.  
    {'Esto refleja un aumento sostenido de las emisiones globales.' if pendiente > 0 else
     'Se observa una mejora gradual en la reducción de emisiones.' if pendiente < 0 else
     'Los valores se mantienen relativamente estables durante el período.'}
    """
    st.markdown(f"<div style='background-color:{color};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
                unsafe_allow_html=True)

# ------------------------------------------
# EXPORTACIÓN
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv,
                       file_name="co2_emisiones_filtradas.csv", mime="text/csv")
with col2:
    import plotly.io as pio
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button("🖼️ Descargar gráfico (HTML interactivo)",
                       data=html_bytes, file_name="grafico_co2.html", mime="text/html")
