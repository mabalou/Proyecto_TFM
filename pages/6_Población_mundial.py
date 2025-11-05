# ==========================================
# 6_Población_mundial.py — versión con resumen lateral + ejes ampliados + estilo homogéneo
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
# VISUALIZACIÓN PRINCIPAL + RESUMEN LATERAL
# ------------------------------------------
st.subheader("📈 Evolución demográfica")

if df_filtrado.empty:
    st.info("Selecciona países y un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
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

        # Ejes y fuentes más grandes
        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )

        if usar_escala_log:
            fig.update_yaxes(type="log", title="Población (escala logarítmica)")

        # Tendencia
        if mostrar_tendencia:
            for pais in paises_sel:
                df_pais = df_filtrado[df_filtrado["País"] == pais]
                if len(df_pais) > 1:
                    x = df_pais["Año"].values.reshape(-1, 1)
                    y = df_pais["Población"].values
                    modelo = LinearRegression().fit(x, y)
                    y_pred = modelo.predict(x)
                    fig.add_scatter(x=df_pais["Año"], y=y_pred, mode="lines", name=f"Tendencia {pais}",
                                    line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_reciente = df_filtrado[df_filtrado["Año"] == df_filtrado["Año"].max()]
        pais_max = df_reciente.loc[df_reciente["Población"].idxmax(), "País"]
        valor_max = df_reciente["Población"].max()
        pais_min = df_reciente.loc[df_reciente["Población"].idxmin(), "País"]
        valor_min = df_reciente["Población"].min()
        media = df_filtrado.groupby("País")["Población"].mean().mean()

        st.markdown(f"""
        - 👑 **Mayor población:** {pais_max} ({valor_max:,.0f})  
        - 🌱 **Menor población:** {pais_min} ({valor_min:,.0f})  
        - 🌍 **Media general:** {media:,.0f}  
        - 📆 **Periodo:** {rango[0]}–{rango[1]}  
        - 🧭 **Países analizados:** {", ".join(paises_sel)}  
        """)

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Población media por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby(["Década", "País"])["Población"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Población", color="País",
                     barmode="group", labels={"Población": "Población media", "Década": "Década"},
                     title="Evolución de la población media por década")
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN HASTA 2100
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    st.subheader("🔮 Proyección hasta 2100")
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
# CONCLUSIONES AUTOMÁTICAS (corregido)
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

    bloques_html = []
    for pais, coef in tendencias.items():
        tendencia = "ascendente" if coef > 0 else "descendente" if coef < 0 else "estable"
        color_fondo = "#006666" if coef > 0 else "#2e8b57" if coef < 0 else "#555555"
        icono = "📈" if coef > 0 else "📉" if coef < 0 else "⚖️"

        bloque = f"""
        <div style='background-color:{color_fondo};
                    padding:1rem;
                    border-radius:10px;
                    color:white;
                    margin-bottom:10px;'>
            {icono} La población de <b>{pais}</b> muestra una tendencia <b>{tendencia}</b>,
            con un cambio medio de <b>{coef:,.0f} hab/año</b>.
        </div>
        """
        bloques_html.append(bloque)

    st.markdown("".join(bloques_html), unsafe_allow_html=True)

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
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
