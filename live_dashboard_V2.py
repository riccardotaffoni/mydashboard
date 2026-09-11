import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from zoneinfo import ZoneInfo

from utils.utils import read_from_ftp, get_remote_mtime


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(page_title="MTRIAGAS Advanced Analysis",layout="wide")

FILE_PATH = "opt/veostrading/veostrading_repos/MTRIAGAS/data/"
FILE_NAME = "data_graph.ftr"


# ------------------------------------------------------------
# FINESTRA TEMPORALE DINAMICA
# ------------------------------------------------------------
# Numero di quarti d'ora prima/dopo quello corrente da mostrare

PLOT_BEFORE = 2
PLOT_AFTER = 12

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
# FINESTRA TEMPORALE DEL GRAFICO
# ============================================================

plot_start = current_quarter - timedelta(minutes=15 * PLOT_BEFORE)
plot_end = current_quarter + timedelta(minutes=15 * (PLOT_AFTER + 1))
plot_start = plot_start.replace(tzinfo=None)
plot_end = plot_end.replace(tzinfo=None)

print("----------------------------------------")
print(f"Current time:      {now}")
print(f"Current quarter:   QH {quarter_number}")
print(f"Quarter start:     {current_quarter}")
print(f"Plot start:        {plot_start}")
print(f"Plot end:          {plot_end}")
print("----------------------------------------")


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
            f"Errore: {e}"
        )

        return pd.DataFrame(), None

# Timestamp remoto del file
mtime = get_remote_mtime(filename=FILE_NAME,path=FILE_PATH)

# Caricamento dati
df, current_mtime = load_data(mtime)

# ============================================================
# SIDEBAR — CONTROLLI ANALISTA
# ============================================================

st.sidebar.header("📊 Componenti Potenza")

sw_sbil = st.sidebar.checkbox("Mostra QTY SBIL",value=True)

sw_levl = st.sidebar.checkbox("Mostra QTY LEVL",value=True)

sw_must = st.sidebar.checkbox("Mostra QTY MUST",value=True)

sw_flex = st.sidebar.checkbox("Mostra QTY FLEX",value=True)

st.sidebar.divider()


st.sidebar.header("🎨 Opzioni Grafico")
dark_mode = st.sidebar.toggle("Modalità Scura",value=True)
show_zones = st.sidebar.checkbox("Mostra Fasce Motore",value=True)
# ============================================================
# INFORMAZIONI FINESTRA TEMPORALE
# ============================================================

st.sidebar.divider()

st.sidebar.markdown(f"""**Quarto corrente:** QH {quarter_number}
    **Orario:** {current_quarter.strftime('%H:%M')}
    **Finestra:** -{PLOT_BEFORE} / +{PLOT_AFTER} QH""")

# ============================================================
# FILTRO DATI
# ============================================================

if not df.empty:
    df_plot = df[(df['delivery_start'] >= plot_start) &(df['delivery_start'] < plot_end)].copy()
else:
    df_plot = pd.DataFrame()

print("DATAFRAME PLOT:")
print(df_plot.head())


# ============================================================
# HEADER
# ============================================================

st.title("🚀 Dashboard MTRIAGAS")
style = ("font-size: 0.85rem; color: gray;")
col_t1, col_t2 = st.columns(2)

# ------------------------------------------------------------
# Ultima modifica dati
# ------------------------------------------------------------

with col_t1:

    if current_mtime is not None:

        mtime_dt = datetime.fromtimestamp(current_mtime,ZoneInfo("Europe/Rome")).strftime('%H:%M:%S %d/%m')
        st.markdown(f"""<p style='{style}'>📂 <b>Ultima modifica dati:</b> {mtime_dt}</p>""",unsafe_allow_html=True)

# ------------------------------------------------------------
# Ultimo controllo
# ------------------------------------------------------------

with col_t2:

    st.markdown(f"""<p style='{style} text-align: right;'>🔄 <b>Ultimo controllo:</b> {last_attempt}</p>""",unsafe_allow_html=True)


# ============================================================
# INFORMAZIONI QUARTO CORRENTE
# ============================================================

st.markdown(f"""<div style="font-size: 0.9rem;color: gray;margin-bottom: 10px;">📍 
                <b>QH corrente:</b> {quarter_number}&nbsp;&nbsp;|&nbsp;&nbsp;🕒 
                <b>Ora:</b> {current_quarter.strftime('%H:%M')}&nbsp;&nbsp;|&nbsp;&nbsp;
                📈 <b>Visualizzazione:</b>{plot_start.strftime('%H:%M')}→ {plot_end.strftime('%H:%M')}</div>""",unsafe_allow_html=True)


# ============================================================
# GRAFICO
# ============================================================

if df_plot.empty:
    st.warning("Nessun dato trovato nella finestra temporale corrente.")
else:
    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    template = ('plotly_dark'if dark_mode else 'plotly_white')


    # --------------------------------------------------------
    # FIGURA
    # --------------------------------------------------------

    fig = go.Figure()


    # ========================================================
    # 1. BASE POWER
    # ========================================================

    fig.add_trace(
        go.Bar(
            x=df_plot['delivery_start'],
            y=df_plot['power'],

            name='Base Power',

            marker_color=(
                'rgba(135, 135, 130, 0.5)'
            ),

            hoverinfo='x+y',

            customdata=df_plot[
                ['cost', 'price_imb']
            ].values,

            hovertemplate=(
                "Ora: %{x}<br>"
                "Power: %{y} MW<br>"
                "Cost: %{customdata[0]}"
                "<extra></extra>"
            )
        )
    )


    # ========================================================
    # 2. COMPONENTI POTENZA
    # ========================================================

    def add_component(
        fig,
        df,
        column,
        name,
        pattern_shape,
        switch
    ):

        if switch and column in df.columns:

            colors = df[column].apply(
                lambda q:
                    'rgba(0,128,0,0.3)'
                    if q >= 0
                    else
                    'rgba(255,0,0,0.3)'
            ).tolist()


            pnl_col = (
                f'PNL_{column.split("_")[1]}_expected'
            )


            if pnl_col in df.columns:

                customdata = df[
                    [pnl_col, 'power']
                ].values

            else:

                customdata = df[
                    ['power']
                ].values


            fig.add_trace(
                go.Bar(

                    x=df['delivery_start'],

                    y=df[column],

                    base=df['power'],

                    name=name,

                    marker=dict(
                        color=colors,
                        pattern=dict(
                            shape=pattern_shape,
                            fgcolor='black'
                        )
                    ),

                    customdata=customdata,

                    hovertemplate=(
                        "QTY: %{y}<br>"
                        "Expected PNL: "
                        "%{customdata[0]:.3f}"
                        "<extra></extra>"
                    )
                )
            )


    add_component(fig,df_plot,'QTY_SBIL','SBIL','/',sw_sbil)

    add_component(fig,df_plot,'QTY_LEVL','LEVL','+',sw_levl)

    add_component(fig,df_plot,'QTY_MUST','MUST','x',sw_must)

    add_component(fig,df_plot,'QTY_FLEX','FLEX','.',sw_flex)

    # ========================================================
    # 3. LINEE FI
    # ========================================================

    for col, name in [('fi_up', 'FI UP'),('fi_down', 'FI DOWN')]:

        if col in df_plot.columns:

            fig.add_scatter(
                x=df_plot['delivery_start'],
                y=df_plot[col],
                mode='lines',
                name=name,
                line=dict(color='black',dash='dot',width=2))

# ========================================================
    # 4. FASCE MOTORE
    # ========================================================

    shapes = []
    annotations = []


    if show_zones:
        regime_colors = {
            '1_engine':'rgba(0,176,80,0.25)',

            '2_engine':'rgba(255,192,0,0.25)',
            '3_engine':'rgba(255,65,54,0.25)'}


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
                            size=10
                        )
                    )
                )


    # ========================================================
    # 5. LINEA ORA CORRENTE
    # ========================================================

    shapes.append(

        dict(

            type='line',

            xref='x',
            yref='paper',

            x0=now,
            x1=now,

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
    # 6. LAYOUT
    # ========================================================

    fig.update_layout(

        template=template,

        barmode='overlay',

        height=700,

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


    # ========================================================
    # 7. PLOT
    # ========================================================

    st.plotly_chart(
        fig,
        width='stretch'
    )


    # ========================================================
    # 8. TABELLA
    # ========================================================

    with st.expander(
        "🔍 Tabella Dati"
    ):

        st.dataframe(
            df_plot,
            width='stretch'
        )
