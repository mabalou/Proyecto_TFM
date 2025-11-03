# ==========================================
# 4_Hielo_marino.py
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
st.markdown("""
Analiza la evolución de la extensión del hielo marino en el **Ártico** y el **Antártico** desde 1978.  
Explora tendencias, variaciones por décadas, comparaciones regionales y conclusiones automáticas.
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
        raise ValueError(f"El archivo {archivo} no contiene las columnas esperadas. Columnas detectadas: {list(df.columns)}")
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
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

region = st.sidebar.selectbox("🌍 Selecciona la región", ["Ártico", "Antártico"])
tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
min_year, max_year = 1978, 2024
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1980, max_year))

mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
comparar_regiones = st.sidebar.checkbox("🌐 Comparar ambas regiones", value=True)

# ------------------------------------------
# CARGA Y FILTRADO
# ------------------------------------------
df = cargar_datos(region)
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
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

# Línea de tendencia
if mostrar_tendencia and not df_filtrado.empty:
    x = df_filtrado["Año"].values.reshape(-1, 1)
    y = df_filtrado["Extensión"].values
    modelo = LinearRegression().fit(x, y)
    y_pred = modelo.predict(x)
    coef = modelo.coef_[0]
    fig.add_scatter(x=df_filtrado["Año"], y=y_pred, mode="lines", name="Tendencia",
                    line=dict(color="red", dash="dash", width=2))
    st.markdown(f"📉 La tendencia muestra un cambio de aproximadamente `{coef:.4f}` millones km² por año.")

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    inicio, fin = df_filtrado["Extensión"].iloc[0], df_filtrado["Extensión"].iloc[-1]
    cambio = fin - inicio
    signo = "disminución" if cambio < 0 else "aumento" if cambio > 0 else "estabilidad"

    st.markdown(
        f"📅 Entre **{rango[0]}** y **{rango[1]}**, se observa una **{signo}** "
        f"de aproximadamente **{abs(cambio):.2f} millones km²** en la extensión del hielo marino del **{region}**."
    )
else:
    st.info("Selecciona un rango válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas:
    st.subheader("📊 Media de extensión por década")
    df_decada = df_filtrado.copy()
    df_decada["Década"] = (df_decada["Año"] // 10) * 10
    df_grouped = df_decada.groupby("Década")["Extensión"].mean().reset_index()

    st.dataframe(df_grouped.style.format({"Extensión": "{:.2f}"}))
    fig_dec = px.bar(df_grouped, x="Década", y="Extensión", color="Extensión",
                     color_continuous_scale="Blues",
                     labels={"Extensión": "Extensión promedio (millones km²)"},
                     title=f"Media por década ({region})")
    st.plotly_chart(fig_dec, use_container_width=True)

    decada_min = int(df_grouped.loc[df_grouped["Extensión"].idxmin(), "Década"])
    valor_min = df_grouped["Extensión"].min()
    st.markdown(f"❄️ La menor extensión promedio se registró en la década de **{decada_min}**, con **{valor_min:.2f} millones km²**.")

# ------------------------------------------
# COMPARATIVA ENTRE REGIONES
# ------------------------------------------
if comparar_regiones:
    st.subheader("🌐 Comparativa entre Ártico y Antártico")

    df_comp = cargar_datos_ambos()
    df_comp = df_comp[(df_comp["Año"] >= rango[0]) & (df_comp["Año"] <= rango[1])]

    fig_comp = px.line(df_comp, x="Año", y="Extensión", color="Región",
                       title="Comparativa de extensión del hielo marino por región",
                       labels={"Extensión": "Extensión (millones km²)", "Año": "Año"})
    st.plotly_chart(fig_comp, use_container_width=True)

    artico_media = df_comp[df_comp["Región"] == "Ártico"]["Extensión"].mean()
    antartico_media = df_comp[df_comp["Región"] == "Antártico"]["Extensión"].mean()
    diferencia = artico_media - antartico_media

    st.markdown(
        f"📊 En promedio durante el periodo seleccionado, la extensión del **Ártico** fue de `{artico_media:.2f}` millones km² "
        f"y la del **Antártico** de `{antartico_media:.2f}` millones km² "
        f"({('mayor' if diferencia > 0 else 'menor')} diferencia de `{abs(diferencia):.2f}` millones km²)."
    )

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS CON COLOR
# ------------------------------------------
if not df_filtrado.empty and mostrar_tendencia:
    st.subheader("🧩 Conclusiones automáticas")

    tendencia = "descendente" if coef < 0 else "ascendente" if coef > 0 else "estable"
    frase_tend = (
        "📉 **Disminución constante de la extensión del hielo marino.**" if coef < 0 else
        "📈 **Aumento gradual de la extensión del hielo marino.**" if coef > 0 else
        "➖ **Sin cambios significativos detectables.**"
    )

    color_fondo = "#ffcccc" if coef < 0 else "#ccffcc" if coef > 0 else "#e6e6e6"
    color_texto = "#222"

    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:{color_texto}; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia general en el <b>{region}</b> es <b>{tendencia}</b> ({coef:.4f} millones km²/año).</li>
                <li>El cambio total en el periodo es de <b>{cambio:.2f} millones km²</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em; color:#444;">🔮 Estas conclusiones se actualizan automáticamente al modificar el rango o la región.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

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
