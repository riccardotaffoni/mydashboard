import pandas as pd
from datetime import datetime
from django.shortcuts import render
import plotly.express as px
import plotly.graph_objects as go
import os
from django.conf import settings

UNIT = "UP_MTRIAGASCM_1"
RESOLUTION = "PT15M"
LIMITS = {
    'off': (0, 0),
    '1_engine': (5.1, 7),
    '2_engine': (10.2, 14),
    '3_engine': (15.3, 21),
}

def dashboard_view(request):
    # Percorso al file feather
    file_path = os.path.join(settings.BASE_DIR, "data/data.feather")
    
    # Leggi il dataframe
    if not os.path.exists(file_path):
        return render(request, "dashboard/dashboard.html", {"error": "File data.feather non trovato."})

    df_today = pd.read_feather(file_path)

    # Solo prime 10 colonne
    df_plot = df_today.iloc[:, :10]

    today = datetime.today().date().strftime("%Y-%m-%d")

    if df_plot.empty:
        return render(request, "dashboard/dashboard.html", {"error": f"No data for {today}"})

    df_plot = df_plot.sort_values('delivery_start')

    # Grafico principale
    fig = px.bar(
        df_plot,
        x='delivery_start',
        y='power',
        hover_data=df_plot.columns.tolist()[1:],  # tutte le altre colonne tranne 'delivery_start'
        labels={'delivery_start': 'Delivery start', 'power': 'Power'},
        title=f"Power vs Delivery Start for {today}",
    )
    fig.update_traces(marker_color='rgba(135, 135, 130,0.50)')

    # FI_UP / FI_DOWN come linee
    if 'fi_up' in df_plot.columns and 'fi_down' in df_plot.columns:
        fig.add_scatter(
            x=df_plot['delivery_start'],
            y=df_plot['fi_up'],
            mode='lines',
            name='FI_UP',
            line=dict(color='black', dash='dot', width=2)
        )
        fig.add_scatter(
            x=df_plot['delivery_start'],
            y=df_plot['fi_down'],
            mode='lines',
            name='FI_DOWN',
            line=dict(color='black', dash='dot', width=2)
        )

    # Regimi motore come bande orizzontali
    regime_colors = {
        'off': 'rgba(200,200,200,0.12)',
        '1_engine': 'rgba(0,176,80,0.12)',
        '2_engine': 'rgba(255,192,0,0.12)',
        '3_engine': 'rgba(255,65,54,0.12)'
    }

    shapes = []
    annotations = []
    for regime, (low, high) in LIMITS.items():
        if high <= low:
            continue
        shapes.append({
            'type': 'rect',
            'xref': 'paper',
            'yref': 'y',
            'x0': 0,
            'x1': 1,
            'y0': low,
            'y1': high,
            'fillcolor': regime_colors.get(regime, 'rgba(100,100,100,0.12)'),
            'opacity': 1.0,
            'line': {'width': 0},
            'layer': 'below'
        })
        annotations.append({
            'xref': 'paper',
            'x': 0.01,
            'y': (low + high) / 2,
            'xanchor': 'left',
            'yanchor': 'middle',
            'text': regime.replace('_', ' ').upper(),
            'showarrow': False,
            'font': {'size': 11, 'color': 'rgba(0,0,0,0.7)'},
            'bgcolor': 'rgba(255,255,255,0.0)'
        })

    fig.update_layout(shapes=shapes, annotations=annotations)
    fig.update_layout(barmode='overlay')
    fig.update_xaxes(tickformat="%H:%M\n%Y-%m-%d", tickangle=45)
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=80), height=800, width=1800)

    # Trasforma in HTML da passare al template
    graph_html = fig.to_html(full_html=False)

    return render(request, "dashboard/dashboard.html", {"graph_html": graph_html})
