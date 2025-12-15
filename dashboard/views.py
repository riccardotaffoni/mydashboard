from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.io as pio

# path al tuo file feather
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "data.feather"

@login_required
def dashboard_view(request):
    # Legge il file feather
    df = pd.read_feather(DATA_PATH)

    # Prendi solo le prime 10 colonne
    df_plot = df.iloc[:, :10]

    # Creiamo un grafico per ogni colonna (tranne delivery_start)
    figures = []
    for col in df_plot.columns:
        if col != "delivery_start":
            fig = px.line(df_plot, x="delivery_start", y=col, title=col)
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            figures.append(pio.to_html(fig, full_html=False, include_plotlyjs='cdn'))

    return render(request, r"C:\Users\User\OneDrive - Veos\Desktop\repos_azure\MTRIAGAS\scripts\live_dashboard\mydashboard\dashboard\templates\dashboard.html", {"figures": figures})
