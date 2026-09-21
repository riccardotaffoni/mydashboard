import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from zoneinfo import ZoneInfo

from utils.utils import read_from_ftp, get_remote_mtime


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(page_title="MTRIAGAS ANALISI AVANZATA",layout="wide")

FILE_PATH = "opt/veostrading/veostrading_repos/MTRIAGAS/data/"
FILE_NAME = "data_graph.ftr"

TEST = False

if TEST:
    FILE_PATH = r"C:\Users\Maciej Sakwa\OneDrive - Veos\Desktop\random_checks"

def get_theme(dark_mode):
    if dark_mode:
        return {
            "template": "plotly_dark",
            "page_bg": "#0f172a",
            "sidebar_bg": "#111827",
            "panel_bg": "#1f2937",
            "text": "#e5e7eb",
            "muted": "#9ca3af",
            "grid": "rgba(229, 231, 235, 0.16)",
            "line": "#e5e7eb",
            "base_bar": "rgba(148, 163, 184, 0.48)",
            "positive": "rgba(34, 197, 94, 0.34)",
            "negative": "rgba(248, 113, 113, 0.36)",
            "pattern": "#e5e7eb",
        }

    return {
        "template": "plotly_white",
        "page_bg": "#ffffff",
        "sidebar_bg": "#f8fafc",
        "panel_bg": "#f1f5f9",
        "text": "#0f172a",
        "muted": "#64748b",
        "grid": "rgba(15, 23, 42, 0.14)",
        "line": "#0f172a",
        "base_bar": "rgba(100, 116, 139, 0.38)",
        "positive": "rgba(22, 163, 74, 0.32)",
        "negative": "rgba(220, 38, 38, 0.30)",
        "pattern": "#0f172a",
    }


def apply_dashboard_theme(theme):
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {theme["page_bg"]};
                color: {theme["text"]};
            }}
            [data-testid="stSidebar"] {{
                background-color: {theme["sidebar_bg"]};
            }}
            [data-testid="stHeader"] {{
                background-color: {theme["page_bg"]};
            }}
            [data-testid="stSidebar"] *,
            [data-testid="stMarkdownContainer"],
            [data-testid="stExpander"],
            h1, h2, h3, h4, h5, h6, p, label {{
                color: {theme["text"]};
            }}
            [data-testid="stButton"] button {{
                background-color: {theme["panel_bg"]};
                border: 1px solid {theme["grid"]};
                color: {theme["text"]};
            }}
            [data-testid="stButton"] button p,
            [data-testid="stButton"] button span {{
                color: {theme["text"]} !important;
            }}
            [data-testid="stButton"] button:hover {{
                border-color: {theme["muted"]};
                color: {theme["text"]};
            }}
            [data-testid="stSidebar"] div[role="switch"],
            [data-testid="stToggle"] div[role="switch"],
            [data-testid="stCheckbox"] div[role="switch"] {{
                background-color: {theme["panel_bg"]} !important;
                border: 2px solid {theme["line"]} !important;
                box-shadow: 0 0 0 3px {theme["grid"]} !important;
            }}
            [data-testid="stSidebar"] div[role="switch"] > div,
            [data-testid="stToggle"] div[role="switch"] > div,
            [data-testid="stCheckbox"] div[role="switch"] > div {{
                background-color: {theme["page_bg"]} !important;
                border: 2px solid {theme["line"]} !important;
            }}
            [data-testid="stSidebar"] div[role="switch"][aria-checked="true"],
            [data-testid="stToggle"] div[role="switch"][aria-checked="true"],
            [data-testid="stCheckbox"] div[role="switch"][aria-checked="true"] {{
                background-color: {theme["line"]} !important;
                border-color: {theme["line"]} !important;
            }}
            [data-testid="stSidebar"] div[role="switch"][aria-checked="true"] > div,
            [data-testid="stToggle"] div[role="switch"][aria-checked="true"] > div,
            [data-testid="stCheckbox"] div[role="switch"][aria-checked="true"] > div {{
                background-color: {theme["page_bg"]} !important;
            }}
            [data-testid="stCaptionContainer"],
            .dashboard-muted {{
                color: {theme["muted"]} !important;
            }}
            [data-testid="stExpander"],
            [data-testid="stDataFrame"] {{
                background-color: {theme["panel_bg"]};
            }}
            hr {{
                border-color: {theme["grid"]};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# AUTO-REFRESH
# ============================================================

st_autorefresh(interval=60 * 1000,key="data_watcher")

# ============================================================
# ORARIO ATTUALE
# ============================================================

now = datetime.now(ZoneInfo("Europe/Rome"))

last_attempt = now.strftime('%H:%M:%S %d/%m/%Y')

# ============================================================
# DETERMINAZIONE QUARTO D'ORA CORRENTE
# ============================================================

current_quarter = now.replace(minute=(now.minute // 15) * 15,second=0,microsecond=0)

quarter_number = (current_quarter.hour * 4+ current_quarter.minute // 15+ 1)

# ============================================================
# CARICAMENTO DATI
# ============================================================

@st.cache_data(show_spinner=False)
def load_data(mtime):

    try:

        time.sleep(0.1)

        df, current_mtime = read_from_ftp(
            filename=FILE_NAME,
            path=FILE_PATH,
            return_mtime=True
        )

        df['delivery_start'] = pd.to_datetime(
            df['delivery_start']
        )
        
        df = df.sort_values(
            'delivery_start'
        )

        return df, current_mtime

    except Exception as e:

        st.error(
            f"ERRORE: {e}"
        )

        return pd.DataFrame(), None

@st.cache_data(show_spinner=False)
def load_data_test():

    try:

        time.sleep(0.1)

        df, current_mtime = pd.read_feather(os.path.join(FILE_PATH, FILE_NAME)), os.path.getmtime(os.path.join(FILE_PATH, FILE_NAME))

        df['delivery_start'] = pd.to_datetime(
            df['delivery_start']
        )
        
        df = df.sort_values(
            'delivery_start'
        )

        return df, current_mtime

    except Exception as e:

        st.error(
            f"ERRORE: {e}"
        )

        return pd.DataFrame(), None

# Caricamento dati

if TEST:
    df, current_mtime = load_data_test()
else:
    mtime = get_remote_mtime(filename=FILE_NAME,path=FILE_PATH)
    df, current_mtime = load_data(mtime)

# ============================================================
# SIDEBAR — CONTROLLI ANALISTA
# ============================================================

st.sidebar.header("📊 COMPONENTI POTENZA")

sw_vol = st.sidebar.checkbox("MOSTRA QUANTITA VOLONTARI",value=True)

sw_must = st.sidebar.checkbox("MOSTRA QUANTITA OBBLIGATORI",value=True)

st.sidebar.divider()


st.sidebar.header("🎨 OPZIONI GRAFICO")
dark_mode = st.sidebar.toggle("MODALITA SCURA",value=True)
show_zones = st.sidebar.checkbox("MOSTRA FASCE MOTORE",value=True)

theme = get_theme(dark_mode)
apply_dashboard_theme(theme)

st.sidebar.divider()
st.sidebar.header("FINESTRA TEMPORALE")

max_before = quarter_number - 1
max_after = 96 - quarter_number

st.session_state.setdefault("plot_before_qh", min(2, max_before))
st.session_state.setdefault("plot_after_qh", min(12, max_after))
st.session_state.plot_before_qh = min(st.session_state.plot_before_qh, max_before)
st.session_state.plot_after_qh = min(st.session_state.plot_after_qh, max_after)

if st.sidebar.button("MOSTRA TUTTA LA GIORNATA"):
    st.session_state.plot_before_qh = max_before
    st.session_state.plot_after_qh = max_after

plot_before = st.sidebar.slider(
    "QUARTI PRIMA",
    min_value=0,
    max_value=max_before,
    key="plot_before_qh",
    step=1
)

plot_after = st.sidebar.slider(
    "QUARTI DOPO",
    min_value=0,
    max_value=max_after,
    key="plot_after_qh",
    step=1
)

# ============================================================
# FINESTRA TEMPORALE DEL GRAFICO
# ============================================================

plot_start = current_quarter - timedelta(minutes=15 * plot_before)
plot_end = current_quarter + timedelta(minutes=15 * (plot_after + 1))
plot_start = plot_start.replace(tzinfo=None)
plot_end = plot_end.replace(tzinfo=None)
now_plot = now.replace(tzinfo=None)

print("----------------------------------------")
print(f"Current time:      {now}")
print(f"Current quarter:   QH {quarter_number}")
print(f"Quarter start:     {current_quarter}")
print(f"Plot start:        {plot_start}")
print(f"Plot end:          {plot_end}")
print("----------------------------------------")
# ============================================================
# INFORMAZIONI FINESTRA TEMPORALE
# ============================================================

st.sidebar.divider()

st.sidebar.markdown(f"""**QUARTO CORRENTE:** QH {quarter_number}
    **ORARIO:** {current_quarter.strftime('%H:%M')}
    **FINESTRA:** -{plot_before} / +{plot_after} QH""")

# ============================================================
# FILTRO DATI
# ============================================================

if not df.empty:
    df_plot = df[(df['delivery_start'] >= plot_start) &(df['delivery_start'] < plot_end)].copy()
else:
    df_plot = pd.DataFrame()

if not df_plot.empty:
    if 'QTY_VOLONTARI' in df_plot.columns:
        df_plot['QTY_VOLONTARI_DASH'] = df_plot['QTY_VOLONTARI']
    else:
        vol_qty_cols = [
            c for c in ['QTY_SBIL', 'QTY_LEVL', 'QTY_FLEX']
            if c in df_plot.columns
        ]
        if vol_qty_cols:
            df_plot['QTY_VOLONTARI_DASH'] = df_plot[vol_qty_cols].sum(axis=1)
        else:
            df_plot['QTY_VOLONTARI_DASH'] = 0.0

    if 'PNL_VOLONTARI_expected' in df_plot.columns:
        df_plot['PNL_VOLONTARI_expected_DASH'] = df_plot['PNL_VOLONTARI_expected']
    else:
        vol_pnl_cols = [
            c for c in ['PNL_SBIL_expected', 'PNL_LEVL_expected', 'PNL_FLEX_expected']
            if c in df_plot.columns
        ]
        if vol_pnl_cols:
            df_plot['PNL_VOLONTARI_expected_DASH'] = df_plot[vol_pnl_cols].sum(axis=1)
        else:
            df_plot['PNL_VOLONTARI_expected_DASH'] = 0.0

    if 'QTY_MUST' not in df_plot.columns:
        df_plot['QTY_MUST'] = 0.0
    if 'PNL_MUST_expected' not in df_plot.columns:
        df_plot['PNL_MUST_expected'] = 0.0

print("DATAFRAME PLOT:")
print(df_plot.head())


# ============================================================
# HEADER
# ============================================================

st.title("🚀 CRUSCOTTO MTRIAGAS _ V3")
style = (f"font-size: 0.85rem; color: {theme['muted']};")
col_t1, col_t2 = st.columns(2)

# ------------------------------------------------------------
# Ultima modifica dati
# ------------------------------------------------------------

with col_t1:

    if current_mtime is not None:

        mtime_dt = datetime.fromtimestamp(current_mtime,ZoneInfo("Europe/Rome")).strftime('%H:%M:%S %d/%m')
        st.markdown(f"""<p style='{style}'>📂 <b>ULTIMA MODIFICA DATI:</b> {mtime_dt}</p>""",unsafe_allow_html=True)

# ------------------------------------------------------------
# Ultimo controllo
# ------------------------------------------------------------

with col_t2:

    st.markdown(f"""<p style='{style} text-align: right;'>🔄 <b>ULTIMO CONTROLLO:</b> {last_attempt}</p>""",unsafe_allow_html=True)


# ============================================================
# INFORMAZIONI QUARTO CORRENTE
# ============================================================

st.markdown(f"""<div style="font-size: 0.9rem;color: {theme['muted']};margin-bottom: 10px;">📍 
                <b>QH CORRENTE:</b> {quarter_number}&nbsp;&nbsp;|&nbsp;&nbsp;🕒 
                <b>ORA:</b> {current_quarter.strftime('%H:%M')}&nbsp;&nbsp;|&nbsp;&nbsp;
                📈 <b>VISUALIZZAZIONE:</b>{plot_start.strftime('%H:%M')}→ {plot_end.strftime('%H:%M')}</div>""",unsafe_allow_html=True)


# ============================================================
# GRAFICO
# ============================================================

if df_plot.empty:
    st.warning("NESSUN DATO TROVATO NELLA FINESTRA TEMPORALE CORRENTE.")
else:
    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    template = theme["template"]


    # --------------------------------------------------------
    # FIGURA
    # --------------------------------------------------------

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.72, 0.28],
        subplot_titles=("POTENZA E QUANTITA", "PNL")
    )


    # ========================================================
    # 1. BASE POWER
    # ========================================================

    fig.add_trace(
        go.Bar(
            x=df_plot['delivery_start'],
            y=df_plot['power'],

            name='PROGRAMMA VINCOLANTE',

            marker_color=(
                theme["base_bar"]
            ),

            hoverinfo='x+y',

            customdata=df_plot[
                ['price_imb']
            ].values,

            hovertemplate=(
                "ORA: %{x}<br>"
                "POTENZA: %{y} MW<br>"
                "PREZZO SBILANCIAMENTO: %{customdata[0]}"
                "<extra></extra>"
            )
        ),
        row=1,
        col=1
    )


    # ========================================================
    # 2. COMPONENTI POTENZA
    # ========================================================

    def add_component(
        fig,
        df,
        column,
        pnl_column,
        name,
        pattern_shape,
        switch
    ):

        if switch and column in df.columns:

            pnl_col = pnl_column

            if pnl_col in df.columns:
                customdata = df[[pnl_col, 'power']].values
            else:
                customdata = df[['power']].values

            up_y = df[column].where(df[column] >= 0, other=None)
            down_y = df[column].where(df[column] < 0, other=None)

            fig.add_trace(
                go.Bar(
                    x=df['delivery_start'],
                    y=up_y,
                    base=df['power'],
                    name=f"{name} A SALIRE",
                    marker=dict(
                        color=theme["positive"],
                        pattern=dict(
                            shape=pattern_shape,
                            fgcolor=theme["pattern"]
                        )
                    ),
                    customdata=customdata,
                    legendgroup=name,
                    hovertemplate=(
                        "QUANTITA: %{y}<br>"
                        "PNL PREVISTO: "
                        "%{customdata[0]:.3f}"
                        "<extra></extra>"
                    )
                ),
                row=1,
                col=1
            )

            fig.add_trace(
                go.Bar(
                    x=df['delivery_start'],
                    y=down_y,
                    base=df['power'],
                    name=f"{name} A SCENDERE",
                    marker=dict(
                        color=theme["negative"],
                        pattern=dict(
                            shape=pattern_shape,
                            fgcolor=theme["pattern"]
                        )
                    ),
                    customdata=customdata,
                    legendgroup=name,
                    hovertemplate=(
                        "QUANTITÀ: %{y}<br>"
                        "PNL PREVISTO: "
                        "%{customdata[0]:.3f}"
                        "<extra></extra>"
                    )
                ),
                row=1,
                col=1
            )


    add_component(
        fig,
        df_plot,
        'QTY_VOLONTARI_DASH',
        'PNL_VOLONTARI_expected_DASH',
        'VOLONTARI',
        '',
        sw_vol
    )

    add_component(
        fig,
        df_plot,
        'QTY_MUST',
        'PNL_MUST_expected',
        'OBBLIGATORI',
        '/',
        sw_must
    )

    # ========================================================
    # 3. LINEE FI
    # ========================================================

    for col, name in [('fi_up', 'INTERVALLO DI FATTIBILITA SUPERIORE'),('fi_down', 'INTERVALLO DI FATTIBILITA INFERIORE')]:

        if col in df_plot.columns:

            fig.add_scatter(
                x=df_plot['delivery_start'],
                y=df_plot[col],
                mode='lines',
                name=name,
                line=dict(color=theme["line"],dash='dot',width=2),
                row=1,
                col=1
            )

# ========================================================
    # 4. PNL SECONDARIO
    # ========================================================

    fig.add_scatter(
        x=df_plot['delivery_start'],
        y=df_plot['PNL_expected'],
        mode='lines+markers',
        name='PNL PREVISTO',
        line=dict(color='#2563eb', width=2),
        row=2,
        col=1
    )

    fig.add_scatter(
        x=df_plot['delivery_start'],
        y=df_plot['PNL_realized'],
        mode='lines+markers',
        name='PNL REALIZZATO',
        line=dict(color='#dc2626', width=2),
        row=2,
        col=1
    )

# ========================================================
    # 5. FASCE MOTORE
    # ========================================================

    shapes = []
    annotations = []


    if show_zones:
        regime_colors = {
            '1_engine':'rgba(0,176,80,0.25)',
            '2_engine':'rgba(255,192,0,0.25)',
            '3_engine':'rgba(255,65,54,0.25)'
        }


        day_limits = {

            '1_engine': (df_plot['1_engine_min'].max(),df_plot['1_engine_max'].max()),
            '2_engine': (df_plot['2_engine_min'].max(),df_plot['2_engine_max'].max()),
            '3_engine': (max(df_plot['2_engine_max'].max(),df_plot['3_engine_min'].min()),df_plot['3_engine_max'].max())}


        for regime, (low, high) in day_limits.items():

            if high > low:

                shapes.append(dict(
                        type='rect',
                        xref='paper',yref='y',
                        x0=0,x1=1,
                        y0=low,y1=high,
                        fillcolor=(regime_colors.get(regime)),
                        line_width=0,
                        layer='below'))


                annotations.append(
                    dict(
                        xref='paper',
                        x=0.01,
                        y=(low + high) / 2,
                        text=regime.upper(),
                        showarrow=False,
                        font=dict(
                            size=10,
                            color=theme["text"]
                        )
                    )
                )


    # ========================================================
    # 6. LINEA ORA CORRENTE
    # ========================================================

    shapes.append(

        dict(

            type='line',

            xref='x',
            yref='paper',

            x0=now_plot,
            x1=now_plot,

            y0=0,
            y1=1,

            line=dict(
                color='red',
                width=2,
                dash='dash'
            )
        )
    )


    # ========================================================
    # 7. LAYOUT
    # ========================================================

    fig.update_layout(

        template=template,
        barmode='overlay',
        height=840,
        paper_bgcolor=theme["page_bg"],
        plot_bgcolor=theme["page_bg"],
        font=dict(color=theme["text"]),
        shapes=shapes,
        annotations=annotations,
        margin=dict(
            l=10,
            r=10,
            t=50,
            b=50
        ),

        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02
        )
    )

    fig.update_xaxes(
        gridcolor=theme["grid"],
        linecolor=theme["grid"],
        tickfont=dict(color=theme["text"]),
        title_font=dict(color=theme["text"])
    )

    fig.update_yaxes(
        gridcolor=theme["grid"],
        linecolor=theme["grid"],
        tickfont=dict(color=theme["text"]),
        title_font=dict(color=theme["text"]),
        row=1,
        col=1
    )

    fig.update_yaxes(
        gridcolor=theme["grid"],
        linecolor=theme["grid"],
        tickfont=dict(color=theme["text"]),
        title_font=dict(color=theme["text"]),
        row=2,
        col=1
    )

    # ========================================================
    # 8. PLOT
    # ========================================================

    st.plotly_chart(
        fig,
        width='stretch'
    )

    # ========================================================
    # 9. TABELLA
    # ========================================================

    with st.expander(
        "🔍 TABELLA DATI"
    ):

        st.dataframe(
            df_plot,
            width='stretch'
        )
