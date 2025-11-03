# ==========================================
# 6_Población_mundial.py — Versión avanzada
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
st.set_page_config(page_title="🌍 Población Mundial", layout="wide")
st.title("🌍 Evolución de la población mundial")
st.markdown("""
Analiza la evolución de la población por país o región a lo largo del tiempo.  
Explora tendencias, medias por década y proyecciones hasta el año 2100.
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

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

paises = sorted(df["País"].unique().tolist())
paises_seleccionados = st.sidebar.multiselect("Selecciona países o regiones", paises, default=["Spain", "United States"])

min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1980, max_year))

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
usar_escala_log = st.sidebar.checkbox("🧮 Usar escala logarítmica", value=False)
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ------------------------------------------
# FILTRADO DE DATOS
# ------------------------------------------
df_filtrado = df[(df["País"].isin(paises_seleccionados)) & (df["Año"].between(*rango))]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Año", y="Población", color="País", markers=True,
                  title="Evolución de la población", labels={"Población": "Población", "Año": "Año"})
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Año", y="Población", color="País",
                  title="Evolución de la población", labels={"Población": "Población", "Año": "Año"})
else:
    fig = px.bar(df_filtrado, x="Año", y="Población", color="País",
                 title="Evolución de la población", labels={"Población": "Población", "Año": "Año"})

if usar_escala_log:
    fig.update_yaxes(type="log", title="Población (escala logarítmica)")

# ------------------------------------------
# TENDENCIA Y MODELOS
# ------------------------------------------
tendencias = {}
if mostrar_tendencia or mostrar_prediccion:
    for pais in paises_seleccionados:
        df_pais = df_filtrado[df_filtrado["País"] == pais]
        if len(df_pais) > 1:
            x = df_pais["Año"].values.reshape(-1, 1)
            y = df_pais["Población"].values
            modelo = LinearRegression().fit(x, y)
            y_pred = modelo.predict(x)
            pendientes = modelo.coef_[0]
            tendencias[pais] = pendientes

            if mostrar_tendencia:
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
    st.markdown(f"📊 En el año **{df_reciente['Año'].max()}**, el país con mayor población fue **{pais_max}** con **{valor_max:,.0f} habitantes.**")

    if len(paises_seleccionados) > 1:
        tendencia_global = np.mean(list(tendencias.values())) if tendencias else 0
        simbolo = "📈" if tendencia_global > 0 else "📉" if tendencia_global < 0 else "⚖️"
        st.markdown(f"{simbolo} **Tendencia media global:** {tendencia_global:,.0f} habitantes/año en los países seleccionados.")
else:
    st.info("Selecciona un rango y país válidos para generar conclusiones.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas:
    st.subheader("📊 Media de población por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby(["Década", "País"])["Población"].mean().reset_index()
    st.dataframe(df_grouped.style.format({"Población": "{:,.0f}"}))

    fig_dec = px.bar(df_grouped, x="Década", y="Población", color="País",
                     barmode="group", labels={"Población": "Población media", "Década": "Década"},
                     title="Evolución de la población media por década")
    if usar_escala_log:
        fig_dec.update_yaxes(type="log", title="Población media (escala logarítmica)")
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN HASTA 2100
# ------------------------------------------
if mostrar_prediccion:
    st.subheader("🔮 Proyección de población hasta 2100")
    fig_pred = px.line(title="Proyecciones de población (hasta 2100)",
                       labels={"x": "Año", "y": "Población"})

    for pais in paises_seleccionados:
        df_pais = df[df["País"] == pais]
        if len(df_pais) > 1:
            x = df_pais["Año"].values.reshape(-1, 1)
            y = df_pais["Población"].values
            modelo = LinearRegression().fit(x, y)
            x_pred = np.arange(x.max()+1, 2101).reshape(-1, 1)
            y_pred = modelo.predict(x_pred)
            fig_pred.add_scatter(x=x_pred.flatten(), y=y_pred, mode="lines", name=pais)
    if usar_escala_log:
        fig_pred.update_yaxes(type="log")
    st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# 🧩 CONCLUSIONES AUTOMÁTICAS CON COLOR (ESTILO UNIFICADO)
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")

if not df_filtrado.empty and tendencias:
    # Caso 1: un solo país seleccionado
    if len(paises_seleccionados) == 1:
        pais = paises_seleccionados[0]
        coef_val = list(tendencias.values())[0]
        tendencia = (
            "ascendente" if coef_val > 0
            else "descendente" if coef_val < 0
            else "estable"
        )

        # Colores coherentes con el resto del dashboard
        color_fondo = "#ffcccc" if coef_val > 0 else "#ccffcc" if coef_val < 0 else "#e6e6e6"
        color_texto = "#222"

        # Década más poblada
        df_decada = df_filtrado.copy()
        df_decada["Década"] = (df_decada["Año"] // 10) * 10
        medias_decadas = df_decada.groupby("Década")["Población"].mean()
        decada_max = medias_decadas.idxmax()
        valor_max = medias_decadas.max()

        # Frase contextual
        frase_tend = (
            "📈 **Aumento sostenido de la población.**" if coef_val > 0 else
            "📉 **Reducción o estancamiento demográfico.**" if coef_val < 0 else
            "➖ **Estabilidad poblacional.**"
        )

        st.markdown(
            f"""
            <div style="background-color:{color_fondo}; color:{color_texto};
                        padding:15px; border-radius:12px; border:1px solid #bbb;">
                <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
                <ul>
                    <li>La tendencia poblacional de <b>{pais}</b> es <b>{tendencia}</b> en el periodo analizado.</li>
                    <li>El cambio medio anual estimado es de <b>{coef_val:,.0f} habitantes</b>.</li>
                    <li>La década más poblada fue la de <b>{int(decada_max)}</b>, con una media de <b>{valor_max:,.0f} habitantes</b>.</li>
                </ul>
                <p>{frase_tend}</p>
                <p style="font-size:0.9em; color:#444;">
                    🔮 Estas conclusiones se actualizan automáticamente al modificar el rango o el país seleccionado.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Caso 2: varios países seleccionados
    elif len(paises_seleccionados) > 1:
        df_tend = pd.DataFrame(list(tendencias.items()), columns=["País", "Crecimiento medio (hab/año)"])
        df_tend = df_tend.sort_values("Crecimiento medio (hab/año)", ascending=False)

        pais_top = df_tend.iloc[0]["País"]
        valor_top = df_tend.iloc[0]["Crecimiento medio (hab/año)"]
        tendencia_general = "ascendente" if valor_top > 0 else "descendente" if valor_top < 0 else "estable"

        color_fondo = "#ffcccc" if valor_top > 0 else "#ccffcc" if valor_top < 0 else "#e6e6e6"

        st.markdown(
            f"""
            <div style="background-color:{color_fondo}; color:#222;
                        padding:15px; border-radius:12px; border:1px solid #bbb;">
                <h4>📋 <b>Conclusión General del Análisis ({rango[0]}–{rango[1]})</b></h4>
                <ul>
                    <li>El país con mayor crecimiento poblacional medio es <b>{pais_top}</b>,
                        con un incremento de <b>{valor_top:,.0f} hab/año</b>.</li>
                    <li>La tendencia global es <b>{tendencia_general}</b> en el periodo analizado.</li>
                </ul>
                <p>💡 Estos resultados reflejan la evolución demográfica desigual entre las regiones seleccionadas.</p>
                <p style="font-size:0.9em; color:#444;">
                    🔮 Las conclusiones se actualizan automáticamente al cambiar países o años.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("📈 **Ranking de tendencias por país:**")
        st.dataframe(df_tend.style.format({"Crecimiento medio (hab/año)": "{:,.0f}"}))

else:
    st.info("Selecciona uno o más países con datos válidos para generar conclusiones.")

# ------------------------------------------
# DESCARGAS SEGURAS (evita fallo de Kaleido)
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

# 📄 Descarga de CSV
with col1:
    try:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv,
                           file_name="datos_filtrados.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

# 🖼️ Descarga de imagen o alternativa
with col2:
    try:
        from io import BytesIO
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                           file_name="grafico.png", mime="image/png")
    except Exception as e:
        st.warning("⚠️ No se pudo generar la imagen en Streamlit Cloud. "
                   "Descarga el gráfico interactivo o los datos.")
        # alternativa: HTML interactivo
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")

