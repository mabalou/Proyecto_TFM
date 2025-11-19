# ==========================================
# 6_Población_mundial.py — versión homogénea y mejorada
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------
st.set_page_config(page_title="🌍 Población Mundial", layout="wide")
st.title("🌍 Evolución de la población mundial")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la evolución de la **población mundial** desde 1960 hasta la actualidad.  

    🔍 **Incluye:**
    - Visualizaciones interactivas suavizadas.  
    - Tendencias lineales y medias por década.  
    - Proyecciones hasta **2100 con intervalo de confianza del 95 %**.  
    - Conclusiones automáticas y descarga de datos.
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
from pymongo import MongoClient

@st.cache_data
def cargar_datos():
    uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client["tfm_datos"]
    coll = db["socioeconomico_population_by_country"]

    docs = list(coll.find({}, {"_id":0}))
    df = pd.DataFrame(docs)

    df = df.rename(columns={
        "Country Name": "País",
        "Year": "Año",
        "Value": "Población"
    })

    df = df.dropna(subset=["País", "Año", "Población"])
    df["Año"] = df["Año"].astype(int)
    df["Población"] = pd.to_numeric(df["Población"], errors="coerce")

    return df

df = cargar_datos()
paises = sorted(df["País"].unique().tolist())
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())

# ------------------------------------------
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
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

paises_sel = st.session_state.paises_seleccionados
rango = st.session_state.rango
tipo_grafico = st.session_state.tipo_grafico
usar_escala_log = st.session_state.usar_escala_log
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

# ------------------------------------------
# FILTRADO + SUAVIZADO
# ------------------------------------------
df_filtrado = df[(df["País"].isin(paises_sel)) & (df["Año"].between(*rango))].copy()
df_filtrado["Suavizada"] = df_filtrado.groupby("País")["Población"].transform(
    lambda x: x.rolling(window=3, center=True, min_periods=1).mean()
)

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL + RESUMEN LATERAL
# ------------------------------------------
st.subheader("📈 Evolución demográfica global")

if df_filtrado.empty:
    st.info("Selecciona países y un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    # --- Gráfico principal ---
    with col1:
        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Año", y="Suavizada", color="País", markers=True,
                          labels={"Suavizada": "Población", "Año": "Año"},
                          title="Evolución de la población (suavizada)")
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Año", y="Suavizada", color="País",
                          labels={"Suavizada": "Población", "Año": "Año"})
        else:
            fig = px.bar(df_filtrado, x="Año", y="Suavizada", color="País",
                         labels={"Suavizada": "Población", "Año": "Año"})

        if usar_escala_log:
            fig.update_yaxes(type="log", title="Población (escala logarítmica)")

        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15),
            legend_title_text="País"
        )

        # Tendencia lineal
        if mostrar_tendencia:
            for pais in paises_sel:
                df_p = df_filtrado[df_filtrado["País"] == pais]
                if len(df_p) > 1:
                    X, Y = df_p["Año"].values.reshape(-1, 1), df_p["Suavizada"].values
                    modelo = LinearRegression().fit(X, Y)
                    Y_pred = modelo.predict(X)
                    fig.add_scatter(x=df_p["Año"], y=Y_pred, mode="lines",
                                    name=f"Tendencia {pais}",
                                    line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    # --- Resumen lateral ---
    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_reciente = df_filtrado[df_filtrado["Año"] == df_filtrado["Año"].max()]
        pais_max = df_reciente.loc[df_reciente["Suavizada"].idxmax(), "País"]
        valor_max = df_reciente["Suavizada"].max()
        pais_min = df_reciente.loc[df_reciente["Suavizada"].idxmin(), "País"]
        valor_min = df_reciente["Suavizada"].min()
        media = df_filtrado.groupby("País")["Suavizada"].mean().mean()

        st.markdown(f"""
        - 👑 **Mayor población:** {pais_max} ({valor_max:,.0f})  
        - 🌱 **Menor población:** {pais_min} ({valor_min:,.0f})  
        - 🌍 **Media general:** {media:,.0f}  
        - 📆 **Periodo:** {rango[0]}–{rango[1]}  
        - 🧭 **Países analizados:** {", ".join(paises_sel)}  
        """)

        # 🔧 Filtros debajo del resumen (compatibles con el botón del header)
        if st.session_state.get("ui_show_filters", True):
            st.markdown("### ⚙️ Ajustar visualización")
            colf1, colf2 = st.columns(2)
            with colf1:
                st.multiselect("🌍 Selecciona países o regiones", paises, default=paises_sel, key="paises_seleccionados")
                st.slider("📆 Rango de años", min_year, max_year, st.session_state.rango, key="rango")
                st.selectbox("📊 Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
            with colf2:
                st.checkbox("📈 Mostrar tendencia", value=mostrar_tendencia, key="mostrar_tendencia")
                st.checkbox("📊 Media por décadas", value=mostrar_decadas, key="mostrar_decadas")
                st.checkbox("🔮 Incluir modelo predictivo", value=mostrar_prediccion, key="mostrar_prediccion")
                st.checkbox("🧮 Escala logarítmica", value=usar_escala_log, key="usar_escala_log")

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Población media por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = ((df_dec["Año"] // 10) * 10).astype(int)
    df_grouped = df_dec.groupby(["Década", "País"])["Suavizada"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Suavizada", color="País",
                     barmode="group", labels={"Suavizada": "Población media", "Década": "Década"},
                     title="Evolución de la población media por década")
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN HASTA 2100 CON IC 95 %
# ------------------------------------------
if mostrar_prediccion and not df_filtrado.empty:
    st.subheader("🔮 Proyección de población hasta 2100")
    fig_pred = px.line(title="Proyecciones demográficas (IC 95 %)",
                       labels={"x": "Año", "y": "Población"})

    for pais in paises_sel:
        df_pais = df[df["País"] == pais]
        if len(df_pais) > 5:
            X = df_pais["Año"].values.reshape(-1, 1)
            Y = df_pais["Población"].values
            modelo = LinearRegression().fit(X, Y)
            future = np.arange(df_pais["Año"].max() + 1, 2101).reshape(-1, 1)
            y_pred = modelo.predict(future)
            resid = Y - modelo.predict(X)
            s = np.std(resid)
            y_upper = y_pred + 1.96 * s
            y_lower = y_pred - 1.96 * s

            fig_pred.add_scatter(x=future.ravel(), y=y_pred, mode="lines", name=pais)
            fig_pred.add_scatter(x=future.ravel(), y=y_upper, mode="lines",
                                 line=dict(color="cyan", width=1), name=f"{pais} IC 95 % sup.")
            fig_pred.add_scatter(x=future.ravel(), y=y_lower, mode="lines",
                                 fill="tonexty", fillcolor="rgba(0,191,255,0.2)",
                                 line=dict(color="cyan", width=1),
                                 name=f"{pais} IC 95 % inf.")

    st.plotly_chart(fig_pred, use_container_width=True)
    st.success("📊 Las proyecciones muestran las posibles trayectorias hasta 2100 con intervalo de confianza del 95 %.")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")

if not df_filtrado.empty:
    bloques_html = []
    for pais in paises_sel:
        df_p = df_filtrado[df_filtrado["País"] == pais]
        if len(df_p) > 1:
            X, Y = df_p["Año"].values.reshape(-1, 1), df_p["Suavizada"].values
            modelo = LinearRegression().fit(X, Y)
            coef = modelo.coef_[0]
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
                con un cambio medio estimado de <b>{coef:,.0f} hab/año</b>.
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
    import plotly.io as pio
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button("🖼️ Descargar gráfico (HTML interactivo)",
                       data=html_bytes, file_name="grafico_poblacion.html", mime="text/html")
