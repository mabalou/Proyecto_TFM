
# Análisis visual de la evolución del cambio climático mediante datos abiertos

**Autor:** Marcos Abal Outeda  
**Máster in Big Data & Visual Analytics**  
**Repositorio:** [https://github.com/mabalou/Proyecto_TFM](https://github.com/mabalou/Proyecto_TFM)

---

## 1. Descripción general

El presente proyecto tiene como objetivo analizar y visualizar la evolución del cambio climático mediante el uso de datos abiertos de organismos internacionales.  
La aplicación, desarrollada en **Streamlit**, permite explorar de forma interactiva indicadores relacionados con el clima, la energía, las emisiones y factores socioeconómicos, combinando análisis descriptivo, correlacional y predictivo.

El desarrollo se enmarca dentro del Trabajo de Fin de Máster del **Máster in Big Data & Visual Analytics**, y busca mostrar el potencial de la analítica visual y las herramientas de ciencia de datos para la comprensión de fenómenos complejos como el cambio climático.

---

## 2. Estructura del proyecto

```
Proyecto_TFM/
│
├── data/
│   ├── energia/
│   ├── gases/
│   ├── socioeconomico/
│   ├── temperatura/
│   └── sea_level/
│
├── pages/
│   ├── 00_Inicio.py
│   ├── 1_Emisiones_de_CO2.py
│   ├── 2_Temperatura_global.py
│   ├── 3_Nivel_del_mar.py
│   ├── 4_Energía_renovable.py
│   ├── 5_Energía_no_renovable.py
│   ├── 6_PIB_y_emisiones.py
│   ├── 7_Población_y_emisiones.py
│   ├── 8_Consumo_energético_por_fuente.py
│   ├── 9_Análisis_multivariable.py
│   └── 10_Mapas_interactivos.py
│
├── requirements.txt
└── README.md
```

---

## 3. Fuentes de datos

Los conjuntos de datos empleados proceden de organismos de referencia y se publican bajo licencias abiertas. Las principales fuentes son:

- **Our World in Data (OWID)**: series históricas de emisiones, consumo energético, PIB y población.  
- **NASA GISS**: anomalías de temperatura global y nivel medio del mar.  
- **NOAA (National Oceanic and Atmospheric Administration)**: concentraciones atmosféricas de gases de efecto invernadero.  
- **Banco Mundial**: datos socioeconómicos agregados por país.  

Cada archivo CSV en la carpeta `data/` incluye información estructurada con las variables, unidades y años correspondientes.

---

## 4. Requisitos del sistema

El proyecto ha sido desarrollado y probado en **Python 3.11**.  
Se recomienda el uso de un entorno virtual independiente.

### Dependencias principales
El proyecto requiere las siguientes librerías, especificadas en el archivo `requirements.txt`:

- Streamlit  
- Pandas  
- NumPy  
- Plotly  
- Scikit-learn  
- Kaleido (opcional, para exportación de gráficos)  
- OpenPyXL  
- Python-dateutil

---

## 5. Instalación y ejecución

### 5.1. Clonar el repositorio
```bash
git clone https://github.com/mabalou/Proyecto_TFM.git
cd Proyecto_TFM
```

### 5.2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate       # En Linux/Mac
venv\Scripts\activate        # En Windows
```

### 5.3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5.4. Ejecutar la aplicación
```bash
streamlit run 00_Inicio.py
```

La aplicación se abrirá automáticamente en el navegador predeterminado (por defecto en [http://localhost:8501](http://localhost:8501)).

---

## 6. Descripción funcional

La aplicación está organizada en distintas secciones accesibles desde el menú lateral de Streamlit:

1. **Inicio:** contextualiza el proyecto y las fuentes de datos.  
2. **Emisiones de CO₂:** evolución histórica y comparativa por países.  
3. **Temperatura global:** análisis de tendencias térmicas desde 1880.  
4. **Nivel del mar:** variación del nivel medio global a lo largo del tiempo.  
5. **Energía renovable / no renovable:** comparación del uso energético global por tipo de fuente.  
6. **PIB y emisiones:** relación entre crecimiento económico y emisiones de CO₂.  
7. **Población y emisiones:** impacto demográfico sobre las emisiones.  
8. **Consumo energético por fuente:** análisis detallado por tipo de energía.  
9. **Análisis multivariable:** correlaciones globales y por país entre variables climáticas y socioeconómicas.  
10. **Mapas interactivos:** representación espacial de indicadores por país y año.

Cada sección incluye:
- Visualizaciones interactivas desarrolladas con **Plotly**.  
- Resúmenes automáticos y conclusiones generadas dinámicamente.  
- Opciones de exportación de datos y gráficos (CSV, PNG o HTML).  

---

## 7. Implementación técnica

El sistema se basa en la integración de herramientas de análisis y visualización en Python:
- **Streamlit:** para la interfaz interactiva.  
- **Pandas / NumPy:** procesamiento y agregación de datos.  
- **Plotly Express:** creación de gráficos dinámicos.  
- **Scikit-learn:** modelos de regresión lineal simples para proyecciones y tendencias.  
- **Kaleido:** exportación opcional de gráficos estáticos.  

Se han aplicado técnicas de preprocesamiento de datos, normalización y análisis estadístico para garantizar la coherencia y consistencia de la información.

---

## 8. Licencia y reconocimiento

Este proyecto se distribuye bajo licencia **MIT**, que permite su uso y modificación citando la fuente original.  
Las bases de datos utilizadas pertenecen a los organismos mencionados y mantienen sus respectivas licencias abiertas de uso público.

---

## 9. Enlace a la aplicación

La versión desplegada del proyecto se encuentra disponible en Streamlit Cloud:

**[https://cambioclimaticotfm.streamlit.app](https://cambioclimaticotfm.streamlit.app)**
