# ==========================================
# 6_Población_mundial.py — versión sincronizada con header
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------
st.set_page_config(page_title="🌍 Población Mundial", layout="wide")
st.title("🌍 Evolución de la población mundial")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Explora la evolución de la **población mundial** desde 1960 hasta la actualidad.  
    Analiza países o regiones, **tendencias por década**, comparativas y **proyecciones demográficas hasta 2100**.
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/socioeconomico/population_by_country.csv")
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "country name": "País",
        "year": "Año",
        "value": "Población"
    })
    df = df[["Año", "País", "Población"]].dropna()
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
    df["Población"] = pd.to_numeric(df["Población"], errors="coerce")
    return df.dropna()

df = cargar_datos()
paises = sorted(df["País"].unique().tolist())
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())

# ------------------------------------------
# ESTADO Y FILTROS (controlados por el header)
# ------------------------------------------
defaults = {
    "ui_show_filters": False,
    "paises_seleccionados": ["Spain", "United States"],
    "rango": (1980, max_year),
    "tipo_grafico": "Línea",
    "usar_escala_log": False,
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.multiselect("🌍 Selecciona países o regiones", paises, key="paises_seleccionados")
        st.slider("📆 Rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.selectbox("📊 Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.checkbox("🧮 Usar escala logarítmica", value=st.session_state.usar_escala_log, key="usar_escala_log")
        st.checkbox("📈 Mostrar tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")

paises_sel = st.session_state.paises_seleccionados
rango = st.session_state.rango
tipo_grafico = st.session_state.tipo_grafico
usar_escala_log = st.session_state.usar_escala_log
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

# ------------------------------------------
# FILTRADO
# ------------------------------------------
df_filtrado = df[(df["País"].isin(paises_sel)) & (df["Año"].between(*rango))]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
st.subheader("📈 Evolución demográfica")

if df_filtrado.empty:
    st.info("Selecciona países y un rango de años válido para visualizar los datos.")
else:
    if tipo_grafico == "Línea":
        fig = px.line(df_filtrado, x="Año", y="Población", color="País", markers=True,
                      labels={"Población": "Población", "Año": "Año"},
                      title="Evolución de la población")
    elif tipo_grafico == "Área":
        fig = px.area(df_filtrado, x="Año", y="Población", color="País",
                      labels={"Población": "Población", "Año": "Año"},
                      title="Evolución de la población")
    else:
        fig = px.bar(df_filtrado, x="Año", y="Población", color="País",
                     labels={"Población": "Población", "Año": "Año"},
                     title="Evolución de la población")

    if usar_escala_log:
        fig.update_yaxes(type="log", title="Población (escala logarítmica)")

    # Tendencias lineales
    if mostrar_tendencia:
        for pais in paises_sel:
            df_pais = df_filtrado[df_filtrado["País"] == pais]
            if len(df_pais) > 1:
                x = df_pais["Año"].values.reshape(-1, 1)
                y = df_pais["Población"].values
                modelo = LinearRegression().fit(x, y)
                y_pred = modelo.predict(x)
                fig.add_scatter(x=df_pais["Año"], y=y_pred, mode="lines", name=f"Tendencia {pais}",
                                line=dict(dash="dash", width=2))

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    df_reciente = df_filtrado[df_filtrado["Año"] == df_filtrado["Año"].max()]
    pais_max = df_reciente.loc[df_reciente["Población"].idxmax(), "País"]
    valor_max = df_reciente["Población"].max()
    st.markdown(f"📊 En **{int(df_reciente['Año'].max())}**, el país con mayor población fue **{pais_max}** con **{valor_max:,.0f} habitantes.**")
else:
    st.info("Selecciona un rango y país válidos para generar conclusiones.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    with st.expander("📊 Media de población por década", expanded=True):
        df_dec = df_filtrado.copy()
        df_dec["Década"] = (df_dec["Año"] // 10) * 10
        df_grouped = df_dec.groupby(["Década", "País"])["Población"].mean().reset_index()
        st.dataframe(df_grouped.style.format({"Población": "{:,.0f}"}), use_container_width=True)

        fig_dec = px.bar(df_grouped, x="Década", y="Población", color="País",
                         barmode="group", labels={"Población": "Población media", "Década": "Década"},
                         title="Evolución de la población media por década")
        st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN HASTA 2100
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    with st.expander("🔮 Proyección hasta 2100", expanded=True):
        fig_pred = px.line(title="Proyecciones de población (hasta 2100)",
                           labels={"x": "Año", "y": "Población"})
        for pais in paises_sel:
            df_pais = df[df["País"] == pais]
            if len(df_pais) > 1:
                x = df_pais["Año"].values.reshape(-1, 1)
                y = df_pais["Población"].values
                modelo = LinearRegression().fit(x, y)
                x_pred = np.arange(x.max() + 1, 2101).reshape(-1, 1)
                y_pred = modelo.predict(x_pred)
                fig_pred.add_scatter(x=x_pred.flatten(), y=y_pred, mode="lines", name=pais)
        st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")

if not df_filtrado.empty:
    tendencias = {}
    for pais in paises_sel:
        df_pais = df_filtrado[df_filtrado["País"] == pais]
        if len(df_pais) > 1:
            x = df_pais["Año"].values.reshape(-1, 1)
            y = df_pais["Población"].values
            modelo = LinearRegression().fit(x, y)
            tendencias[pais] = modelo.coef_[0]

    if len(paises_sel) == 1:
        pais = paises_sel[0]
        coef = list(tendencias.values())[0]
        color_fondo = "#ffcccc" if coef > 0 else "#ccffcc" if coef < 0 else "#e6e6e6"
        st.markdown(
            f"""
            <div style="background-color:{color_fondo}; padding:15px; border-radius:12px;">
                <h4>📋 Conclusión ({rango[0]}–{rango[1]})</h4>
                <p>La población de <b>{pais}</b> muestra una tendencia 
                {'ascendente 📈' if coef > 0 else 'descendente 📉' if coef < 0 else 'estable ⚖️'} 
                con un cambio medio de <b>{coef:,.0f} hab/año</b>.</p>
            </div>
            """, unsafe_allow_html=True
        )
    else:
        df_tend = pd.DataFrame(list(tendencias.items()), columns=["País", "Crecimiento medio (hab/año)"])
        st.dataframe(df_tend.style.format({"Crecimiento medio (hab/año)": "{:,.0f}"}))

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="poblacion_filtrada.csv", mime="text/csv")

with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name="grafico_poblacion.png", mime="image/png")
    except Exception:
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)", data=html_bytes,
                           file_name="grafico_poblacion.html", mime="text/html")
