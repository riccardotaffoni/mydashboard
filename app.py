from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from flask import Flask, request, Response
from functools import wraps

# -----------------------------
# AUTH (password molto semplice)
# -----------------------------
USERNAME = "user"
PASSWORD = "pass"

def check_auth(auth):
    return auth and auth.username == USERNAME and auth.password == PASSWORD

def authenticate():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not check_auth(auth):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# -----------------------------
# Flask server + Dash app
# -----------------------------
server = Flask(__name__)

@server.route('/')
@requires_auth
def home():
    return app.index()

app = Dash(__name__, server=server, url_base_pathname='/dashboard/')


# -----------------------------
# Funzione per caricare dati
# -----------------------------
def load_data():
    return pd.read_csv("data.csv")  # aggiornato ogni 15 min


# -----------------------------
# Layout dashboard
# -----------------------------
app.layout = html.Div([
    html.H1("Dashboard Interattiva"),
    
    html.Label("Filtro categoria:"),
    dcc.Dropdown(id="category-filter", multi=False),
    
    html.Button("Refresh dati", id="refresh-btn", n_clicks=0),
    
    dcc.Graph(id="main-graph"),
])


# -----------------------------
# Callback per aggiornare opzioni filtri
# -----------------------------
@app.callback(
    Output("category-filter", "options"),
    Output("category-filter", "value"),
    Input("refresh-btn", "n_clicks")
)
def update_filters(n):
    df = load_data()
    categories = sorted(df["categoria"].unique())
    return categories, categories[0]


# -----------------------------
# Callback per aggiornare il grafico
# -----------------------------
@app.callback(
    Output("main-graph", "figure"),
    Input("category-filter", "value"),
    Input("refresh-btn", "n_clicks")
)
def update_graph(category, n):
    df = load_data()
    df = df[df["categoria"] == category]
    
    fig = px.line(df, x="timestamp", y="valore", title=f"Categoria: {category}")
    return fig


# -----------------------------
# Avvio server
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
