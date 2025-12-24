import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

from utils.utils import read_from_ftp
# --- CONFIGURAZIONE ---
st.set_page_config(page_title="MTRIAGAS Advanced Analysis", layout="wide")
FILE_PATH = "opt/veostrading/veostrading_repos/MTRIAGAS/data/"
FILE_NAME= "data_graph.ftr"

# --- AUTO-REFRESH (10 secondi) ---
st_autorefresh(interval=10 * 1000, key="data_watcher")
last_attempt = datetime.now().strftime('%H:%M:%S')

# --- CARICAMENTO DATI ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
        time.sleep(0.1)
        df,current_mtime = read_from_ftp(filename=FILE_NAME, path=FILE_PATH, return_mtime=True)
        df['delivery_start'] = pd.to_datetime(df['delivery_start'])
        return df.sort_values('delivery_start'), current_mtime
    except Exception as e:
        st.error(f"Errore: {e}")
        return pd.DataFrame(), None

#current_mtime = os.path.getmtime(FILE_PATH) if os.path.exists(FILE_PATH) else 0
df, current_mtime = load_data()
# --- SIDEBAR: CONTROLLI ANALISTA ---
st.sidebar.header("📊 Componenti Potenza")
sw_sbil = st.sidebar.checkbox("Mostra QTY SBIL", value=True)
sw_levl = st.sidebar.checkbox("Mostra QTY LEVL", value=True)
sw_must = st.sidebar.checkbox("Mostra QTY MUST", value=True)
sw_flex = st.sidebar.checkbox("Mostra QTY FLEX", value=True)

st.sidebar.divider()
st.sidebar.header("🎨 Opzioni Grafico")
dark_mode = st.sidebar.toggle("Modalità Scura", value=False)
show_zones = st.sidebar.checkbox("Mostra Fasce Motore", value=True)

if st.sidebar.button("🔄 Reset Filtri"):
    st.session_state.start_val = df['delivery_start'].max() - timedelta(hours=24)
    st.session_state.end_val = df['delivery_start'].max() + timedelta(hours=24)

# --- GESTIONE DATE ---
if not df.empty:
    if 'start_val' not in st.session_state:
        st.session_state.start_val = df['delivery_start'].max() - timedelta(hours=24)
    if 'end_val' not in st.session_state:
        st.session_state.end_val = df['delivery_start'].max() + timedelta(hours=24)

    start_dt = st.sidebar.datetime_input("Inizio", value=st.session_state.start_val)
    end_dt = st.sidebar.datetime_input("Fine", value=st.session_state.end_val)
    st.session_state.start_val, st.session_state.end_val = start_dt, end_dt

    df_plot = df[(df['delivery_start'] >= pd.to_datetime(start_dt)) & 
                 (df['delivery_start'] <= pd.to_datetime(end_dt))].copy()
else:
    df_plot = pd.DataFrame()

# --- HEADER ---
st.title("🚀 Dashboard MTRIAGAS")
# Definiamo uno stile comune per entrambi i testi
style = "font-size: 0.85rem; color: gray;"

col_t1, col_t2 = st.columns(2)

with col_t1:
    mtime_dt = datetime.fromtimestamp(current_mtime).strftime('%H:%M:%S %d/%m')
    st.markdown(f"<p style='{style}'>📂 <b>Ultima modifica dati:</b> {mtime_dt}</p>", 
                unsafe_allow_html=True)

with col_t2:
    st.markdown(f"<p style='{style} text-align: right;'>🔄 <b>Ultimo controllo (auto-refresh):</b> {last_attempt}</p>", 
                unsafe_allow_html=True)

if df_plot.empty:
    st.warning("Nessun dato trovato.")
else:
    # --- COSTRUZIONE GRAFICO (LOGICA ANALISTA) ---
    template = 'plotly_dark' if dark_mode else 'plotly_white'
    
    # 1. Base: Power Bar
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_plot['delivery_start'],
        y=df_plot['power'],
        name='Base Power',
        marker_color='rgba(135, 135, 130, 0.5)',
        hoverinfo='x+y',
        customdata=df_plot[['cost', 'price_imb']].values,
        hovertemplate="Ora: %{x}<br>Power: %{y} MW<br>Cost: %{customdata[0]}<extra></extra>"
    ))

    # 2. Funzione per aggiungere componenti (SBIL, LEVL, MUST, FLEX)
    def add_component(fig, df, column, name, pattern_shape, switch):
        if switch and column in df.columns:
            colors = df[column].apply(lambda q: 'rgba(0,128,0,0.3)' if q >= 0 else 'rgba(255,0,0,0.3)').tolist()
            pnl_col = f'PNL_{column.split("_")[1]}_expected'
            
            fig.add_trace(go.Bar(
                x=df['delivery_start'],
                y=df[column],
                base=df['power'],
                name=name,
                marker=dict(color=colors, pattern=dict(shape=pattern_shape, fgcolor='black')),
                customdata=df[[pnl_col, 'power']].values if pnl_col in df.columns else df[['power']].values,
                hovertemplate="QTY: %{y}<br>Expected PNL: %{customdata[0]:.3f}<extra></extra>"
            ))

    add_component(fig, df_plot, 'QTY_SBIL', 'SBIL', '/', sw_sbil)
    add_component(fig, df_plot, 'QTY_LEVL', 'LEVL', '+', sw_levl)
    add_component(fig, df_plot, 'QTY_MUST', 'MUST', 'x', sw_must)
    add_component(fig, df_plot, 'QTY_FLEX', 'FLEX', '.', sw_flex)

    # 3. Linee FI (Dotted)
    for col, name in [('fi_up', 'FI UP'), ('fi_down', 'FI DOWN')]:
        if col in df_plot.columns:
            fig.add_scatter(x=df_plot['delivery_start'], y=df_plot[col], mode='lines', 
                            name=name, line=dict(color='black', dash='dot', width=2))

    # 4. Fasce Motore (Regime)
    shapes = []
    annotations = []
    if show_zones:
        regime_colors = {'1_engine': 'rgba(0,176,80,0.1)', '2_engine': 'rgba(255,192,0,0.1)', '3_engine': 'rgba(255,65,54,0.1)'}
        day_limits = {
            '1_engine': (df_plot['1_engine_min'].min(), df_plot['1_engine_max'].max()),
            '2_engine': (df_plot['2_engine_min'].min(), df_plot['2_engine_max'].max()),
            '3_engine': (max(df_plot['2_engine_max'].max(), df_plot['3_engine_min'].min()), df_plot['3_engine_max'].max())
        }
        for regime, (low, high) in day_limits.items():
            if high > low:
                shapes.append(dict(type='rect', xref='paper', yref='y', x0=0, x1=1, y0=low, y1=high, 
                                   fillcolor=regime_colors.get(regime), line_width=0, layer='below'))
                annotations.append(dict(xref='paper', x=0.01, y=(low+high)/2, text=regime.upper(), showarrow=False, font=dict(size=10)))

    # 5. Linea Tempo Corrente
    now = datetime.now()
    shapes.append(dict(type='line', xref='x', yref='paper', x0=now, x1=now, y0=0, y1=1, line=dict(color='red', width=2, dash='dash')))

    # Layout Finale
    fig.update_layout(
            template=template,
            barmode='overlay',
            height=700,
            shapes=shapes,
            annotations=annotations,
            margin=dict(l=10, r=10, t=50, b=50),
            # Modifica qui:
            legend=dict(
                orientation="v",      # Verticale
                yanchor="top",        # Ancorata in alto
                y=1,                  # Posizione y (1 è il top del grafico)
                xanchor="left",       # Ancorata a sinistra rispetto alla sua coordinata x
                x=1.02                # Spostata leggermente a destra oltre il bordo del grafico (1.0)
            )
        )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- TABELLA ---
    with st.expander("🔍 Tabella Dati"):
        st.dataframe(df_plot, use_container_width=True)