import plotly.express as px

def grafico_temperatura(df):
    fig = px.line(
        df,
        x="Year",
        y="J-D",
        labels={"Year": "Año", "J-D": "Anomalía media anual (°C)"},
        title="Anomalía de temperatura global (NASA GISTEMP)",
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    return fig
