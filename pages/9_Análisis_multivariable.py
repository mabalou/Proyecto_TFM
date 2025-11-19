# ==========================================
# 9_Análisis_multivariable.py — responsive con filtros, resumen lateral,
# ejes grandes, medias por década, predicción 2100 y conclusiones homogéneas
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# -------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -------------------------------------------------
st.set_page_config(page_title="🔗 Análisis multivariable", layout="wide")
st.title("🔗 Análisis multivariable: clima ↔ sociedad")

# --- CSS para mantener los filtros debajo del resumen ---
st.markdown(
    """
    <style>
    /* Subir bloque derecho (resumen + filtros) */
    div[data-testid="column"]:nth-of-type(2) {
        margin-top: -6rem !important;
    }
    /* Reducir espacio entre resumen y filtros */
    div[data-testid="stMarkdown"] + div[data-testid="stMarkdown"] {
        margin-top: -1.2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.expander("ℹ️ **Descripción del análisis**", expanded=False):
    st.markdown("""
    En esta sección se realiza un **análisis multivariable** que combina datos
    de **clima global** (temperatura, gases, nivel del mar, energía)
    y **socioeconómicos** (PIB, población, emisiones por país).
    """)

# -------------------------------------------------
# UTILIDADES
# -------------------------------------------------
def _safe_read_csv(path, **kwargs):
    for args in ({}, {"engine": "python"}, {"comment": "#", "engine": "python"}):
        try:
            return pd.read_csv(path, **{**kwargs, **args})
        except Exception:
            pass
    return pd.DataFrame()

def _lin_trend(x_year: pd.Series, y: pd.Series):
    x_clean = pd.to_numeric(pd.Series(x_year).squeeze(), errors="coerce")
    y_clean = pd.to_numeric(pd.Series(y).squeeze(), errors="coerce")
    m = (~x_clean.isna()) & (~y_clean.isna())
    if m.sum() < 2:
        return np.nan, None
    X = x_clean[m].values.reshape(-1, 1)
    Y = y_clean[m].values
    lr = LinearRegression().fit(X, Y)
    return float(lr.coef_[0]), lr

def _zscore(df_num: pd.DataFrame):
    df_num = df_num.apply(pd.to_numeric, errors="coerce")
    return (df_num - df_num.mean()) / df_num.std(ddof=0)

def _style_axes(fig, font_size=15, axis_title=17):
    fig.update_layout(
        xaxis_title_font=dict(size=axis_title),
        yaxis_title_font=dict(size=axis_title),
        font=dict(size=font_size),
        legend_title_text="Variable"
    )
    return fig

TEAL = "#0d6b6b"

# -------------------------------------------------
# CARGA GLOBAL (clima + energía agregada mundial) DESDE MONGODB
# -------------------------------------------------
from pymongo import MongoClient

@st.cache_data
def load_global_sources():

    uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client["tfm_datos"]

    dfs = []

    # ---------------- TEMPERATURA ----------------
    col_temp = db["temperatura_global_nasa"]
    t = pd.DataFrame(list(col_temp.find({}, {"_id": 0})))

    if not t.empty:
        t.columns = t.columns.str.strip()
        if "Year" in t.columns:
            num_cols = [c for c in t.columns if c not in ["Year"]]
            t["Temp_anom_C"] = pd.to_numeric(t[num_cols], errors="coerce").mean(axis=1)
            t = t.rename(columns={"Year": "Año"})[["Año", "Temp_anom_C"]].dropna()
            t["Temp_anom_C"] = t["Temp_anom_C"].rolling(5, center=True, min_periods=1).mean()
        else:
            t = pd.DataFrame(columns=["Año", "Temp_anom_C"])
    dfs.append(t)

    # ---------------- GASES ----------------
    def _load_gas_mongo(collection, out_col):
        df = pd.DataFrame(list(db[collection].find({}, {"_id": 0})))
        if df.empty or "year" not in df.columns:
            return pd.DataFrame(columns=["Año", out_col])
        df = df.rename(columns={"year": "Año"})
        if "average" in df.columns:
            df = df.rename(columns={"average": out_col})
        elif "trend" in df.columns:
            df = df.rename(columns={"trend": out_col})
        else:
            return pd.DataFrame(columns=["Año", out_col])
        df[out_col] = pd.to_numeric(df[out_col], errors="coerce")
        return df[["Año", out_col]].dropna()

    co2 = _load_gas_mongo("gases_co2_global", "CO2_ppm")
    ch4 = _load_gas_mongo("gases_ch4_global", "CH4_ppb")
    n2o = _load_gas_mongo("gases_n2o_global", "N2O_ppb")

    dfs += [co2, ch4, n2o]

    # ---------------- NIVEL DEL MAR ----------------
    sl = pd.DataFrame(list(db["sea_level_nasa"].find({}, {"_id": 0})))
    if not sl.empty and "Fecha" in sl.columns:
        sl["Fecha"] = pd.to_datetime(sl["Fecha"], errors="coerce")
        sl["Año"] = sl["Fecha"].dt.year
        sl = sl.groupby("Año", as_index=False)["Nivel_mm"].mean()
        sl = sl.rename(columns={"Nivel_mm": "SeaLevel_mm"})
    dfs.append(sl)

    # ---------------- ENERGÍA GLOBAL ----------------
    ene = pd.DataFrame(list(db["energia_energy_consuption_by_source"].find({}, {"_id": 0})))

    if not ene.empty:
        ene.columns = ene.columns.str.strip().str.lower()
        if "year" in ene.columns:
            ene = ene.rename(columns={"year": "Año"})
        ene = ene.groupby("Año", as_index=False).sum(numeric_only=True)

        nice = {
            "coal_consumption": "Coal_TWh",
            "oil_consumption": "Oil_TWh",
            "gas_consumption": "Gas_TWh",
            "renewables_consumption": "Renewables_TWh",
            "fossil_fuel_consumption": "Fossils_TWh",
        }
        ene = ene.rename(columns=nice)
        ene = ene[["Año"] + [v for v in nice.values() if v in ene.columns]]

    dfs.append(ene)

    # ---------------- UNIFICAR ----------------
    df = None
    for d in dfs:
        if not d.empty and "Año" in d.columns:
            df = d if df is None else pd.merge(df, d, on="Año", how="outer")

    if df is None:
        return pd.DataFrame(columns=["Año"])

    return df.sort_values("Año").reset_index(drop=True)

# -------------------------------------------------
# CARGA POR PAÍS — DESDE MONGODB
# -------------------------------------------------
@st.cache_data
def load_country_sources():

    uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client["tfm_datos"]

    # -------- PIB --------
    gdp = pd.DataFrame(list(db["socioeconomico_gdp_by_country"].find({}, {"_id": 0})))
    if not gdp.empty:
        gdp = gdp.rename(columns={
            "Country Name": "País",
            "country": "País",
            "Year": "Año",
            "Value": "PIB_USD"
        })
        gdp = gdp[["Año", "País", "PIB_USD"]].dropna()
    else:
        gdp = pd.DataFrame(columns=["Año", "País", "PIB_USD"])

    # -------- POBLACIÓN --------
    pop = pd.DataFrame(list(db["socioeconomico_population_by_country"].find({}, {"_id": 0})))
    if not pop.empty:
        pop = pop.rename(columns={
            "Country Name": "País",
            "country": "País",
            "Year": "Año",
            "Value": "Población"
        })
        pop = pop[["Año", "País", "Población"]].dropna()
    else:
        pop = pd.DataFrame(columns=["Año", "País", "Población"])

    # -------- CO₂ --------
    co2 = pd.DataFrame(list(db["socioeconomico_co2_by_country"].find({}, {"_id": 0})))
    if not co2.empty:
        co2 = co2.rename(columns={
            "Country Name": "País",
            "country": "País",
            "Year": "Año",
            "Value": "CO2_Mt",
            "co2": "CO2_Mt"
        })
        co2 = co2[["Año", "País", "CO2_Mt"]].dropna()
    else:
        co2 = pd.DataFrame(columns=["Año", "País", "CO2_Mt"])

    return gdp, pop, co2

# -------------------------------------------------
# ESTADO DE FILTROS
# -------------------------------------------------
st.session_state.setdefault("ui_show_filters", False)

# =================================================
# TABS
# =================================================
tab1, tab2 = st.tabs(["🌐 Global", "🗺️ Por país"])

# ---------------- GLOBAL -------------------------
with tab1:
    st.subheader("🌐 Variables globales combinadas")

    global_df = load_global_sources()
    if "Año" not in global_df.columns or global_df.empty:
        st.error("No se pudieron cargar variables globales con columna 'Año'. Revisa los CSV.")
        st.stop()

    miny, maxy = int(global_df["Año"].min()), int(global_df["Año"].max())
    vars_disp = [c for c in global_df.columns if c != "Año" and pd.api.types.is_numeric_dtype(global_df[c])]
    defaults_vars = [v for v in ["Temp_anom_C", "CO2_ppm", "SeaLevel_mm", "Fossils_TWh", "Renewables_TWh"] if v in vars_disp] or vars_disp[:4]

    # Filtros (responsive al botón del header)
    defaults_g = {
        "global_cols": defaults_vars,
        "global_rango": (max(miny, 1980), maxy),
        "global_tipo": "Serie normalizada"
    }
    for k, v in defaults_g.items():
        st.session_state.setdefault(k, v)

    if st.session_state.ui_show_filters:
        with st.container(border=True):
            st.subheader("⚙️ Filtros de visualización (Global)")
            st.multiselect("Variables", options=vars_disp, default=st.session_state.global_cols, key="global_cols")
            st.slider("Rango de años", min_value=miny, max_value=maxy, value=st.session_state.global_rango, key="global_rango")
            st.selectbox("Tipo de gráfico", ["Serie normalizada", "Dispersión (dos variables)", "Matriz de correlación"], key="global_tipo")

    cols = st.session_state.global_cols
    rmin, rmax = st.session_state.global_rango
    tipo = st.session_state.global_tipo

    dfg = global_df[global_df["Año"].between(rmin, rmax)].copy()

    if cols and not dfg.empty:
        # Visual principal + Resumen lateral
        c1, c2 = st.columns([3, 1], gap="large")

        with c1:
            if tipo == "Serie normalizada":
                # ✅ Copiar solo columnas seleccionadas
                dfg_plot = dfg[["Año"] + cols].copy()

                # ✅ Agrupar por año (evita efecto escalera si hay varias observaciones por año)
                dfg_plot = dfg_plot.groupby("Año", as_index=False).mean(numeric_only=True)

                # ✅ Suavizar cada variable individualmente (exactamente igual que en 2_Gases)
                for c in cols:
                    dfg_plot[f"{c}_Suavizada"] = (
                        dfg_plot[c]
                        .rolling(window=3, center=True, min_periods=1)
                        .mean()
                    )

                # ✅ Normalizar (z-score) sobre las columnas suavizadas
                suav_cols = [f"{c}_Suavizada" for c in cols]
                z = _zscore(dfg_plot[suav_cols])
                z["Año"] = dfg_plot["Año"]

                # ✅ Formato largo
                z = z.melt(id_vars="Año", var_name="Variable", value_name="Z")
                z["Variable"] = z["Variable"].str.replace("_Suavizada", "", regex=False)

                # ✅ Colores coherentes
                color_map = {
                    "CO2_ppm": "#00BFFF",
                    "CH4_ppb": "#32CD32",
                    "N2O_ppb": "#FF6347",
                    "Temp_anom_C": "#FFA500",
                    "SeaLevel_mm": "#1E90FF",
                    "Fossils_TWh": "#FFB6C1",
                    "Renewables_TWh": "#FF4500"
                }

                # ✅ Gráfico final
                fig = px.line(
                    z, x="Año", y="Z", color="Variable", markers=True,
                    labels={"Z": "Valor normalizado (z-score)", "Año": "Año"},
                    title="Evolución normalizada y suavizada por variable",
                    color_discrete_map=color_map
                )
                fig.update_traces(mode="lines+markers", line=dict(width=3))
                fig = _style_axes(fig)
                st.plotly_chart(fig, use_container_width=True)

            elif tipo == "Dispersión (dos variables)":
                if len(cols) < 2:
                    st.info("Selecciona al menos **dos** variables.")
                else:
                    xvar, yvar = cols[0], cols[1]
                    df2 = dfg.dropna(subset=[xvar, yvar]).copy()
                    fig = px.scatter(
                        df2, x=xvar, y=yvar,
                        color_discrete_sequence=["#00BFFF"],
                        labels={xvar: xvar, yvar: yvar},
                        title=f"Relación entre {yvar} y {xvar}"
                    )
                    fig.update_traces(name=f"{yvar} vs {xvar}", showlegend=True)

                    m, model = _lin_trend(df2[xvar], df2[yvar])
                    if model is not None:
                        xx = np.linspace(df2[xvar].min(), df2[xvar].max(), 100)
                        yy = model.predict(xx.reshape(-1, 1))
                        fig.add_scatter(x=xx, y=yy, mode="lines", name="Tendencia", line=dict(dash="dash", width=2, color="red"))
                    fig = _style_axes(fig)
                    st.plotly_chart(fig, use_container_width=True)

            else:  # Matriz de correlación
                dfc = dfg[cols].apply(pd.to_numeric, errors="coerce").dropna(how="all")
                if dfc.shape[1] < 2:
                    st.info("Selecciona **al menos dos** variables.")
                else:
                    corr = dfc.corr(numeric_only=True)
                    fig = px.imshow(corr, text_auto=".2f", aspect="auto", title="Matriz de correlación (Pearson)")
                    fig = _style_axes(fig)
                    st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("### 🧾 Resumen")
            base = cols[0]
            serie = pd.to_numeric(dfg[base], errors="coerce")
            if serie.notna().sum() >= 2:
                vmin, vmax = float(serie.min()), float(serie.max())
                ymin = int(dfg.loc[serie.idxmin(), "Año"])
                ymax = int(dfg.loc[serie.idxmax(), "Año"])
                media = float(serie.mean())
                m, _ = _lin_trend(dfg["Año"], serie)
                tend = "ascendente" if m > 0 else "descendente" if m < 0 else "estable"
                st.markdown(f"""
                - 📆 **Años:** {rmin}–{rmax}  
                - 🔽 **Mínimo:** {vmin:,.3f} (*{ymin}*)  
                - 🔼 **Máximo:** {vmax:,.3f} (*{ymax}*)  
                - 📊 **Media:** {media:,.3f}  
                - 📈 **Tendencia ({base}):** {tend}
                """)

        # Media por décadas (sobre la 1ª variable seleccionada)
        st.subheader("📊 Media por década")
        tmp = dfg[["Año"] + cols].copy()
        tmp["Década"] = (tmp["Año"] // 10) * 10
        df_dec = tmp.groupby("Década")[cols[0]].mean(numeric_only=True).reset_index().rename(columns={cols[0]: "Valor"})
        fig_dec = px.bar(df_dec, x="Década", y="Valor",
                         labels={"Valor": cols[0]},
                         title=f"Media por década — {cols[0]}")
        fig_dec = _style_axes(fig_dec)
        st.plotly_chart(fig_dec, use_container_width=True)

        # Predicción hasta 2100 (siempre visible)
        st.subheader("🔮 Proyección hasta 2100")
        # Si hay varias variables, usamos el promedio de las seleccionadas
        pred_series = dfg[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        valid = (~dfg["Año"].isna()) & (~pred_series.isna())

        if valid.sum() >= 3:
            X = dfg.loc[valid, "Año"].values.reshape(-1, 1)
            Y = pred_series.loc[valid].values

            # Modelo lineal
            modelo = LinearRegression().fit(X, Y)
            x_pred = np.arange(int(dfg["Año"].max()) + 1, 2101).reshape(-1, 1)
            y_pred = modelo.predict(x_pred)

            # Intervalo de confianza (95 %)
            resid = Y - modelo.predict(X)
            s = np.std(resid)
            y_upper = y_pred + 1.96 * s
            y_lower = y_pred - 1.96 * s

            # Gráfico principal
            fig_pred = px.line(
                x=x_pred.ravel(),
                y=y_pred,
                labels={"x": "Año", "y": f"Proyección ({'promedio' if len(cols) > 1 else cols[0]})"},
                title=f"Predicción hasta 2100 ({'promedio de variables seleccionadas' if len(cols) > 1 else cols[0]})"
            )

            # Añadir bandas de confianza
            fig_pred.add_scatter(
                x=x_pred.ravel(), y=y_upper,
                mode="lines",
                line=dict(color="cyan", width=1),
                name="IC 95 % (superior)"
            )
            fig_pred.add_scatter(
                x=x_pred.ravel(), y=y_lower,
                mode="lines",
                fill="tonexty", fillcolor="rgba(0,191,255,0.2)",
                line=dict(color="cyan", width=1),
                name="IC 95 % (inferior)"
            )

            fig_pred = _style_axes(fig_pred)
            st.plotly_chart(fig_pred, use_container_width=True)

            st.success("🌡️ El modelo predice una **tendencia lineal** hacia 2100 con un **intervalo de confianza del 95 %**.")
        else:
            st.info("Datos insuficientes para proyectar.")

        # Conclusiones automáticas (estilo homogéneo)
        st.subheader("🧩 Conclusiones automáticas")
        concl = []
        # 1) Tendencia de la base
        m, _ = _lin_trend(dfg["Año"], dfg[cols[0]])
        if not pd.isna(m):
            tend = "ascendente" if m > 0 else "descendente" if m < 0 else "estable"
            concl.append(f"• La tendencia de **{cols[0]}** es **{tend}** en **{rmin}–{rmax}**.")
        # 2) Mayor correlación entre pares
        if len(cols) >= 2:
            corr = dfg[cols].apply(pd.to_numeric, errors="coerce").corr().abs()
            iu = np.triu_indices_from(corr, k=1)
            if len(iu[0]) > 0:
                best = np.nanargmax(corr.values[iu])
                i, j = iu[0][best], iu[1][best]
                v1, v2 = corr.index[i], corr.columns[j]
                concl.append(f"• Mayor relación entre **{v1}–{v2}** (|r|={corr.values[iu][best]:.2f}).")
        # 3) Década con mayor actividad relativa (z-score medio absoluto)
        tmp = dfg.copy()
        tmp["Década"] = (tmp["Año"] // 10) * 10
        z = _zscore(tmp[cols]).abs().mean(axis=1)
        tmp["act"] = z
        if not tmp["act"].dropna().empty:
            dec = int(tmp.groupby("Década")["act"].mean().idxmax())
            concl.append(f"• Década con mayor variación relativa: **{dec}**.")
        texto = "<br/>".join(concl) if concl else "Selecciona variables y rango válidos."
        st.markdown(
            f"<div style='background-color:{TEAL};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Configura variables y rango para visualizar resultados.")

# ---------------- POR PAÍS -----------------------
with tab2:
    st.subheader("🗺️ Indicadores por país")
    gdp, pop, co2c = load_country_sources()

    paises = sorted(set(gdp.get("País", pd.Series(dtype=str))) |
                    set(pop.get("País", pd.Series(dtype=str))) |
                    set(co2c.get("País", pd.Series(dtype=str))))

    # Rango de años global disponible
    def _minmax_year(df):
        return (df["Año"].min(), df["Año"].max()) if "Año" in df.columns and not df.empty else (np.nan, np.nan)

    minc = [x for x in _minmax_year(gdp) + _minmax_year(pop) + _minmax_year(co2c) if pd.notna(x)]
    if not minc:
        st.warning("No hay datos por país para construir el rango de años.")
        st.stop()
    miny, maxy = int(np.nanmin(minc)), int(np.nanmax(minc))

    # Métricas disponibles
    all_metrics = []
    if "PIB_USD" in gdp.columns: all_metrics.append("PIB_USD")
    if "Población" in pop.columns: all_metrics.append("Población")
    if "CO2_Mt" in co2c.columns: all_metrics.append("CO2_Mt")

    # Filtros (responsive)
    defaults_c = {
        "country_sel": [p for p in ["Spain", "United States"] if p in paises] or paises[:2],
        "country_rango": (max(miny, 1980), maxy),
        "country_metrics": all_metrics,
        "country_tipo": "Serie (normalizada)"
    }
    for k, v in defaults_c.items():
        st.session_state.setdefault(k, v)

    if st.session_state.ui_show_filters:
        with st.container(border=True):
            st.subheader("⚙️ Filtros de visualización (Por país)")
            st.multiselect("Países/regiones", paises, key="country_sel")
            st.slider("Rango de años", min_value=miny, max_value=maxy, value=st.session_state.country_rango, key="country_rango")
            st.multiselect("Métricas", options=all_metrics, default=st.session_state.country_metrics, key="country_metrics")
            st.selectbox("Vista", ["Serie (normalizada)", "Dispersión (dos métricas)", "Correlación (por países)"], key="country_tipo")

    sel = st.session_state.country_sel
    rmin, rmax = st.session_state.country_rango
    metrica = st.session_state.country_metrics
    vista = st.session_state.country_tipo

    # Construimos panel por país (outer merge por año)
    panel = pd.DataFrame()
    for p in sel:
        d = pd.DataFrame({"Año": list(range(rmin, rmax + 1))})
        d["País"] = p
        if "PIB_USD" in metrica and "PIB_USD" in gdp.columns:
            d = d.merge(gdp[(gdp["País"] == p) & (gdp["Año"].between(rmin, rmax))][["Año", "PIB_USD"]],
                        on="Año", how="left")
        if "Población" in metrica and "Población" in pop.columns:
            d = d.merge(pop[(pop["País"] == p) & (pop["Año"].between(rmin, rmax))][["Año", "Población"]],
                        on="Año", how="left")
        if "CO2_Mt" in metrica and "CO2_Mt" in co2c.columns:
            d = d.merge(co2c[(co2c["País"] == p) & (co2c["Año"].between(rmin, rmax))][["Año", "CO2_Mt"]],
                        on="Año", how="left")
        panel = pd.concat([panel, d], ignore_index=True) if not panel.empty else d

    if not panel.empty and metrica:
        # Visual + Resumen lateral
        c1, c2 = st.columns([3, 1], gap="large")

        with c1:
            if vista == "Serie (normalizada)":
                dfp = panel.dropna(subset=metrica, how="all").copy()
                z_list = []
                for p in sel:
                    sub = dfp[dfp["País"] == p].copy()
                    if sub.empty:
                        continue
                    Z = _zscore(sub[metrica])
                    Z["Año"] = sub["Año"].values
                    Z["País"] = p
                    z_list.append(Z)
                if z_list:
                    z = pd.concat(z_list, ignore_index=True)
                    z = z.melt(id_vars=["Año", "País"], var_name="Variable", value_name="Z")

                    # ✅ Corrección: sin facet_row, con line_dash
                    fig = px.line(
                        z, x="Año", y="Z", color="País", line_dash="Variable",
                        title="Series normalizadas por país y métrica",
                        labels={"Z": "Valor normalizado (z-score)", "Año": "Año"}
                    )
                    fig = _style_axes(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos suficientes para normalizar.")


            elif vista == "Dispersión (dos métricas)":
                if len(metrica) < 2:
                    st.info("Selecciona al menos **dos** métricas.")
                else:
                    xvar, yvar = metrica[0], metrica[1]
                    df2 = panel.dropna(subset=[xvar, yvar])
                    fig = px.scatter(df2, x=xvar, y=yvar, color="País", hover_data=["Año"],
                                     title=f"{yvar} vs {xvar}")
                    m, model = _lin_trend(df2[xvar], df2[yvar])
                    if model is not None:
                        xx = np.linspace(df2[xvar].min(), df2[xvar].max(), 100)
                        yy = model.predict(xx.reshape(-1, 1))
                        fig.add_scatter(x=xx, y=yy, mode="lines", name="Tendencia", line=dict(dash="dash", width=2, color="red"))
                    fig = _style_axes(fig)
                    st.plotly_chart(fig, use_container_width=True)

            else:  # Correlación por países (tabla)
                try:
                    tabla = panel.groupby("País")[metrica].corr().reset_index().rename(columns={"level_1": "Variable2", 0: "r"})
                    st.dataframe(tabla, use_container_width=True)
                except Exception:
                    st.info("No se pudo calcular la correlación con los datos actuales.")

        with c2:
            st.markdown("### 🧾 Resumen")
            # Usamos la primera métrica disponible para el resumen
            base = metrica[0]
            sub = panel.dropna(subset=[base])
            if not sub.empty:
                serie = pd.to_numeric(sub[base], errors="coerce")
                vmin, vmax = float(serie.min()), float(serie.max())
                ymin = int(sub.loc[serie.idxmin(), "Año"])
                ymax = int(sub.loc[serie.idxmax(), "Año"])
                media = float(serie.mean())
                m, _ = _lin_trend(sub["Año"], serie)
                tend = "ascendente" if m > 0 else "descendente" if m < 0 else "estable"
                st.markdown(f"""
                - 📆 **Años:** {rmin}–{rmax}  
                - 🔽 **Mínimo ({base}):** {vmin:,.2f} (*{ymin}*)  
                - 🔼 **Máximo ({base}):** {vmax:,.2f} (*{ymax}*)  
                - 📊 **Media ({base}):** {media:,.2f}  
                - 📈 **Tendencia:** {tend}
                """)

        # Media por década (para la primera métrica)
        st.subheader("📊 Media por década")
        dec = panel.copy()
        dec["Década"] = (dec["Año"] // 10) * 10
        df_dec = dec.groupby(["Década", "País"])[metrica[0]].mean(numeric_only=True).reset_index().rename(columns={metrica[0]: "Valor"})
        fig_dec = px.bar(df_dec, x="Década", y="Valor", color="País",
                         barmode="group",
                         labels={"Valor": metrica[0]},
                         title=f"Media por década — {metrica[0]}")
        fig_dec = _style_axes(fig_dec)
        st.plotly_chart(fig_dec, use_container_width=True)

        # Predicción hasta 2100 (una línea por país sobre la métrica base)
        st.subheader("🔮 Proyección hasta 2100")
        fig_pred = px.line(labels={"x": "Año", "y": metrica[0]}, title=f"Proyección hasta 2100 ({metrica[0]})")
        for p in sel:
            sub = panel[(panel["País"] == p) & (~panel[metrica[0]].isna())]
            if len(sub) >= 3:
                X = sub["Año"].values.reshape(-1, 1)
                Y = pd.to_numeric(sub[metrica[0]], errors="coerce").values
                model = LinearRegression().fit(X, Y)
                x_pred = np.arange(int(sub["Año"].max()) + 1, 2101).reshape(-1, 1)
                y_pred = model.predict(x_pred)
                fig_pred.add_scatter(x=x_pred.ravel(), y=y_pred, mode="lines", name=p)
        fig_pred = _style_axes(fig_pred)
        st.plotly_chart(fig_pred, use_container_width=True)

        # Conclusiones automáticas (una caja, mismas reglas)
        st.subheader("🧩 Conclusiones automáticas")
        outs = []
        for p in sel:
            sub = panel[(panel["País"] == p)]
            if sub.empty: 
                continue
            base = metrica[0]
            m, _ = _lin_trend(sub["Año"], sub[base])
            if pd.notna(m):
                tend = "creciente 📈" if m > 0 else "decreciente 📉" if m < 0 else "estable ⚖️"
                outs.append(f"• **{p}**: {base} {tend} (pendiente media {m:,.0f} /año).")
        texto = "<br/>".join(outs) if outs else "Selecciona países y métricas con datos válidos."
        st.markdown(
            f"<div style='background-color:{TEAL};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Configura países/métricas para visualizar resultados.")

# =================================================
# DESCARGAS SEGURAS Y EXPORTACIÓN
# =================================================
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

# Detecta el DataFrame activo (global o país)
df_export = None
if "dfg" in locals() and isinstance(dfg, pd.DataFrame) and not dfg.empty:
    df_export = dfg.copy()
elif "panel" in locals() and isinstance(panel, pd.DataFrame) and not panel.empty:
    df_export = panel.copy()

# Detecta el último gráfico dibujado
fig_export = None
for cand in ["fig_pred", "fig_dec", "fig"]:
    if cand in locals():
        fig_export = locals()[cand]

with col1:
    if df_export is not None and not df_export.empty:
        try:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("📄 Descargar CSV", data=csv, file_name="analisis_multivariable_datos.csv", mime="text/csv")
        except Exception as e:
            st.error(f"No se pudo generar el CSV: {e}")
    else:
        st.info("⚠️ No hay datos disponibles para exportar.")

with col2:
    if fig_export is not None:
        import plotly.io as pio
        # Exportar directamente en formato HTML interactivo
        html_bytes = pio.to_html(fig_export, full_html=False).encode("utf-8")
        st.download_button(
            "🖼️ Descargar gráfico (HTML interactivo)",
            data=html_bytes,
            file_name="grafico_multivariable.html",
            mime="text/html"
        )
    else:
        st.info("⚠️ No hay gráfico disponible para exportar todavía.")

