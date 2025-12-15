#pip install plotly pandas

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime, timedelta


UNIT = "UP_MTRIAGASCM_1"
RESOLUTION = "PT15M"
LIMITS = {
    'off': (0, 0),
    '1_engine': (5.1, 7),
    '2_engine': (10.2, 14),
    '3_engine': (15.3, 21),}

def graph(df_today):

    today = datetime.today().date().strftime("%Y-%m-%d")

    switch_sbil = True
    switch_levl = True
    switch_must = True
    switch_flex = True

    if df_today.empty:
        print(f"No data for {today}")
    else:
        df_today = df_today.sort_values('delivery_start')
        fig = px.bar(
            df_today,
            x='delivery_start',
            y='power',
            hover_data=['cost', 'price_imb', 'fi_up', 'fi_down'],
            labels={'delivery_start': 'Delivery start', 'power': 'Power'},
            title=f"Power vs Delivery Start for {today}",
        )
        fig.update_traces(marker_color='rgba(135, 135, 130,0.50)')

        # Add dotted red lines for fi_up and fi_down
        fig.add_scatter(
            x=df_today['delivery_start'],
            y=df_today['fi_up'],
            mode='lines',
            name='FI_UP',
            line=dict(color='black', dash='dot', width=2),
            hoverinfo='skip'
        )
        fig.add_scatter(
            x=df_today['delivery_start'],
            y=df_today['fi_down'],
            mode='lines',
            name='FI_DOWN',
            line=dict(color='black', dash='dot', width=2),
            hoverinfo='skip'
        )

        if switch_sbil:
            # color bars green for positive QUANTITY, red for negative
            colors = df_today['QTY_SBIL'].apply(lambda q: 'rgba(0,128,0,0.20)' if q >= 0 else 'rgba(255,0,0,0.20)').tolist()

            fig.add_trace(go.Bar(
                x=df_today['delivery_start'],
                y=df_today['QTY_SBIL'],
                base=df_today['power'],  # set bar bottom equal to power
                name='Quantity_SBIL',
                marker=dict(
                    color=colors,                        # per-bar color
                    pattern=dict(shape='/', fgcolor='black')
                ),
                hovertemplate='Delivery start=%{x}<br>Power=%{customdata[1]:.2f}<br>Quantity=%{y:.2f}<br>Expected PNL=%{customdata[0]:.3f}<extra></extra>',
                customdata=df_today[['PNL_SBIL_expected', 'power']].values
            ))

        if switch_levl:
            # color bars green for positive QUANTITY, red for negative
            colors = df_today['QTY_LEVL'].apply(lambda q: 'rgba(0,128,0,0.20)' if q >= 0 else 'rgba(255,0,0,0.20)').tolist()

            fig.add_trace(go.Bar(
                x=df_today['delivery_start'],
                y=df_today['QTY_LEVL'],
                base=df_today['power'],  # set bar bottom equal to power
                name='Quantity_LEVL',
                marker=dict(
                    color=colors,                        # per-bar color
                    pattern=dict(shape='+', fgcolor='black')
                ),
                hovertemplate='Delivery start=%{x}<br>Power=%{customdata[1]:.2f}<br>Quantity=%{y:.2f}<br>Expected PNL=%{customdata[0]:.3f}<extra></extra>',
                customdata=df_today[['PNL_LEVL_expected', 'power']].values
            ))

        if switch_must:
            # color bars green for positive QUANTITY, red for negative
            colors = df_today['QTY_MUST'].apply(lambda q: 'rgba(0,128,0,0.20)' if q >= 0 else 'rgba(255,0,0,0.20)').tolist()

            fig.add_trace(go.Bar(
                x=df_today['delivery_start'],
                y=df_today['QTY_MUST'],
                base=df_today['power'],  # set bar bottom equal to power
                name='Quantity_MUST',
                marker=dict(
                    color=colors,                        # per-bar color
                    pattern=dict(shape='x', fgcolor='black')
                ),
                hovertemplate='Delivery start=%{x}<br>Power=%{customdata[1]:.2f}<br>Quantity=%{y:.2f}<br>Expected PNL=%{customdata[0]:.3f}<extra></extra>',
                customdata=df_today[['PNL_MUST_expected', 'power']].values
            ))

        if switch_flex:
            # color bars green for positive QUANTITY, red for negative
            colors = df_today['QTY_FLEX'].apply(lambda q: 'rgba(0,128,0,0.20)' if q >= 0 else 'rgba(255,0,0,0.20)').tolist()

            fig.add_trace(go.Bar(
                x=df_today['delivery_start'],
                y=df_today['QTY_FLEX'],
                base=df_today['power'],  # set bar bottom equal to power
                name='Quantity_FLEX',
                marker=dict(
                    color=colors,                        # per-bar color
                    pattern=dict(shape='.', fgcolor='black')
                ),
                hovertemplate='Delivery start=%{x}<br>Power=%{customdata[1]:.2f}<br>Quantity=%{y:.2f}<br>Expected PNL=%{customdata[0]:.3f}<extra></extra>',
                customdata=df_today[['PNL_FLEX_expected', 'power']].values
            ))

        # Add horizontal semi-transparent flat bars for engine operational regions
        # Use xref='paper' so the bands span full plot width and stay when zooming vertically
        regime_colors = {
            'off': 'rgba(200,200,200,0.12)',
            '1_engine': 'rgba(0,176,80,0.12)',
            '2_engine': 'rgba(255,192,0,0.12)',
            '3_engine': 'rgba(255,65,54,0.12)'
        }

        shapes = []
        annotations = []
        for regime, (low, high) in LIMITS.items():
            # skip zero-height regions
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
                'opacity': 1.0,  # color already contains alpha
                'line': {'width': 0},
                'layer': 'below'
            })
            # place a small label at left side of the plot within the band
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

        # update layout with shapes and annotations
        fig.update_layout(shapes=shapes, annotations=annotations)

        # Put bars on top of each other (overlay)
        fig.update_layout(barmode='overlay')
        fig.update_xaxes(tickformat="%H:%M\n%Y-%m-%d", tickangle=45)
        fig.update_layout(margin=dict(l=40, r=20, t=60, b=80), height=800, width=1800)
        fig.show()


def main():

    delta = 0
    test_date = pd.to_datetime(datetime.today().date())

    df_sbil = pd.read_feather("data/data_sbilanciamenti.ftr")
    df_livl = pd.read_feather("data/data_livellamenti.ftr")

    # Merge dataframes on delivery_start
    df_final = df_sbil[['delivery_start', 'power', 'fi_up', 'fi_down', 'price_imb', 'cost', 'QUANTITY', 'PNL', 'PNL_expected']].merge(
    df_livl[['delivery_start', 'no_motori', 'discounted_on', 'discounted_off', 'margin_must', 'margin_flex_up', 'margin_flex_down', 
              'QTY_LEVL', 'QTY_MUST', 'QTY_FLEX', 'PNL_LEVL', 'PNL_MUST', 'PNL_FLEX', 'PNL_LEVL_expected', 'PNL_MUST_expected', 'PNL_FLEX_expected']], on='delivery_start', how='left'
        ).rename(columns={'QUANTITY':'QTY_SBIL', 'PNL':'PNL_SBIL', 'PNL_expected':'PNL_SBIL_expected'})

    # Eliminate overlapping quantities
    mask_flex = df_final['QTY_FLEX'].abs() > df_final['QTY_SBIL'].abs()
    df_final.loc[mask_flex, 'QTY_SBIL'] = 0
    df_final.loc[mask_flex, 'PNL_SBIL'] = 0
    df_final.loc[mask_flex, 'PNL_SBIL_expected'] = 0

    # Filter rows for the current day (uses existing `test_date` and `df_merged`)
    today = pd.to_datetime(test_date).date() - pd.Timedelta(days=delta)
    df_today = df_final[df_final['delivery_start'].dt.date == today].copy()
    print(df_today)
    df_today.to_feather("data/data.feather")
    #graph(df_today)

if __name__ == "__main__":
    main()