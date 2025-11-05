# ==========================================
# 7_PIB_y_crecimiento_económico.py — versión mejorada (resumen lateral + ejes grandes + secciones visibles)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------
st.set_page_config(page_title="💰 PIB y Crecimiento Económico", layout="wide")
st.title("💰 Evolución del PIB por país")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la **evolución del Producto Interior Bruto (PIB)** de los países según los datos del **Banco Mundial**.  
    Permite visualizar **tendencias económicas**, medias por década y **proyecciones hasta 2100**.
    """)

# ------------------------------------------
# CARGA ROBUSTA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/socioeconomico/gdp_by_country.csv")
    df.columns = df.columns.str.strip().str.lower()

    year_col = next((c for c in df.columns if "year" in c), None)
    country_col = next((c for c in df.columns if "country" in c), None)
    value_col = next((c for c in df.columns if c in ["value", "gdp", "pib", "gdp (current us$)", "gdp_usd"] or "gdp" in c), None)

    if not all([year_col, country_col, value_col]):
        st.error(f"⚠️ No se encontraron columnas esperadas en el CSV.\n\nColumnas detectadas: {list(df.columns)}")
        st.stop()

    df = df.rename(columns={
        year_col: "Año",
        country_col: "País",
        value_col: "PIB"
    })

    df = df[["Año", "País", "PIB"]].dropna()
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
    df["PIB"] = pd.to_numeric(df["PIB"], errors="coerce")
    return df.dropna()

df = cargar_datos()
paises = sorted(df["País"].unique())
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())

# ------------------------------------------
# ESTADO Y FILTROS CONTROLADOS POR HEADER
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
# VISUALIZACIÓN PRINCIPAL + RESUMEN LATERAL
# ------------------------------------------
st.subheader("📈 Evolución del PIB")

if df_filtrado.empty:
    st.info("Selecciona países y un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Año", y="PIB", color="País", markers=True,
                          labels={"PIB": "PIB (USD actuales)", "Año": "Año"},
                          title="Evolución del PIB")
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Año", y="PIB", color="País",
                          labels={"PIB": "PIB (USD actuales)", "Año": "Año"},
                          title="Evolución del PIB")
        else:
            fig = px.bar(df_filtrado, x="Año", y="PIB", color="País",
                         labels={"PIB": "PIB (USD actuales)", "Año": "Año"},
                         title="Evolución del PIB")

        # Ejes más grandes
        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )

        if usar_escala_log:
            fig.update_yaxes(type="log", title="PIB (escala logarítmica)")

        # Tendencias lineales
        if mostrar_tendencia:
            for pais in paises_sel:
                df_pais = df_filtrado[df_filtrado["País"] == pais]
                if len(df_pais) > 1:
                    x = df_pais["Año"].values.reshape(-1, 1)
                    y = df_pais["PIB"].values
                    modelo = LinearRegression().fit(x, y)
                    y_pred = modelo.predict(x)
                    fig.add_scatter(x=df_pais["Año"], y=y_pred, mode="lines", name=f"Tendencia {pais}",
                                    line=dict(dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_reciente = df_filtrado[df_filtrado["Año"] == df_filtrado["Año"].max()]
        pais_max = df_reciente.loc[df_reciente["PIB"].idxmax(), "País"]
        valor_max = df_reciente["PIB"].max()
        pais_min = df_reciente.loc[df_reciente["PIB"].idxmin(), "País"]
        valor_min = df_reciente["PIB"].min()
        media = df_filtrado["PIB"].mean()

        st.markdown(f"""
        - 📆 **Años:** {rango[0]}–{rango[1]}  
        - 💹 **PIB máximo:** {pais_max} — ${valor_max:,.0f}  
        - 📉 **PIB mínimo:** {pais_min} — ${valor_min:,.0f}  
        - 🌍 **PIB medio del período:** ${media:,.0f}  
        - 🏷️ **Países seleccionados:** {", ".join(paises_sel)}
        """)

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Media del PIB por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby(["Década", "País"])["PIB"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="PIB", color="País",
                     barmode="group", labels={"PIB": "PIB medio (USD)", "Década": "Década"},
                     title="Evolución del PIB medio por década")
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PROYECCIÓN FUTURA
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    st.subheader("🔮 Proyección del PIB hasta 2100")
    fig_pred = px.line(title="Proyección del PIB hasta 2100", labels={"x": "Año", "y": "PIB (USD actuales)"})
    for pais in paises_sel:
        df_pais = df[df["País"] == pais]
        if len(df_pais) > 1:
            x = df_pais["Año"].values.reshape(-1, 1)
            y = df_pais["PIB"].values
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
            y = df_pais["PIB"].values
            modelo = LinearRegression().fit(x, y)
            tendencias[pais] = modelo.coef_[0]

    color_fondo = "#006666"
    texto = "<ul>"
    for pais, coef in tendencias.items():
        if coef > 0:
            texto += f"<li>📈 <b>{pais}</b>: tendencia ascendente (+{coef:,.0f} USD/año)</li>"
        elif coef < 0:
            texto += f"<li>📉 <b>{pais}</b>: tendencia descendente ({coef:,.0f} USD/año)</li>"
        else:
            texto += f"<li>➖ <b>{pais}</b>: estabilidad económica</li>"
    texto += "</ul>"

    st.markdown(
        f"<div style='background-color:{color_fondo};padding:1rem;border-radius:10px;color:white;'>"
        f"<h4>📋 Conclusión Final ({rango[0]}–{rango[1]})</h4>{texto}</div>",
        unsafe_allow_html=True
    )

# ------------------------------------------
# EXPORTACIÓN
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)

with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="pib_filtrado.csv", mime="text/csv")

with col2:
    import plotly.io as pio
    # Exportar gráfico en formato HTML interactivo (sin Kaleido)
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button(
        "🖼️ Descargar gráfico (HTML interactivo)",
        data=html_bytes,
        file_name="grafico_pib.html",
        mime="text/html"
    )
