# ==========================================
# 00_Inicio.py — Inicio moderno del TFM
# ==========================================
import streamlit as st

st.set_page_config(
    page_title="🌍 Visualizador climático del TFM",
    layout="wide"
)

# --- Encabezado elegante ---
st.markdown("""
<div style="text-align:center; padding-top:1rem;">
    <h1 style="font-size:2.8rem; margin-bottom:0;">🌎 Visualizador climático global del TFM</h1>
    <p style="font-size:1.2rem; color:#bbb;">
        Proyecto interactivo para analizar la evolución del <b>cambio climático global</b> y su relación con la sociedad.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Sección principal: tarjetas ---
st.markdown("### 🧭 Navegación principal")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background-color:#1e1e1e; border-radius:12px; padding:20px; border:1px solid #333;">
        <h3>🌡️ Temperatura</h3>
        <p style="color:#ccc;">Analiza las anomalías térmicas globales por década, estación y región.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background-color:#1e1e1e; border-radius:12px; padding:20px; border:1px solid #333;">
        <h3>🗺️ Mapa climático</h3>
        <p style="color:#ccc;">Explora visualmente la distribución geográfica de emisiones, PIB y población.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background-color:#1e1e1e; border-radius:12px; padding:20px; border:1px solid #333;">
        <h3>🔗 Análisis multivariable</h3>
        <p style="color:#ccc;">Descubre relaciones entre energía, temperatura, PIB y gases de efecto invernadero.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- Breve descripción del proyecto ---
st.markdown("""
### 🎓 Sobre el proyecto
Este trabajo de fin de máster combina **datos climáticos globales**, **indicadores socioeconómicos** y **energía** para ofrecer una visión integradora del impacto humano en el planeta.  
Incluye análisis predictivos, visualizaciones interactivas y conclusiones automáticas.

📘 *Autor:* **Marcos Abal**  
🏫 *Universidad Internacional de La Rioja (UNIR)**  
📅 *Año:* 2025
""")
