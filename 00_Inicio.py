import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="🌍 Visualizador climático del TFM",
    page_icon="🌡️",
    layout="centered"
)

# Título principal
st.title("🌍 Visualizador climático del TFM")

# Introducción general
st.markdown("""
Bienvenido/a al visualizador interactivo del **Trabajo de Fin de Máster**.

Este proyecto tiene como objetivo principal analizar y comunicar el impacto del **cambio climático global** a través de datos históricos y visualizaciones interactivas.

Puedes navegar por las distintas secciones usando el menú lateral.
""")

# Secciones destacadas
st.markdown("""
### 🧭 Navegación disponible:

- **Temperatura**: Analiza las anomalías de temperatura global por estaciones, por década, y más.
- **Mapa global** *(próximamente)*: Visualiza las anomalías climáticas en un mapa mundial.
- **CO₂ y emisiones** *(próximamente)*: Explora la relación entre emisiones de gases de efecto invernadero y el cambio climático.

---

 Sigue explorando y descubre los patrones ocultos en los datos del clima global.
""")

# Footer
st.caption("TFM | Marcos Abal | UNIR")
