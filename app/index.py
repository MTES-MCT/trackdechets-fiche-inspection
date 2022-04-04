import datetime

import pandas as pd
from dash import html, dcc
import plotly.io as pio
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

from app.app import dash_app, extra_config
from app.time_config import time_delta_m, today
import app.data
import app.figures

# Override the 'none' template
pio.templates["gouv"] = go.layout.Template(
    layout=dict(
        font=dict(family="Marianne"),
        title=dict(
            x=0.01
        ),
        paper_bgcolor='rgb(238, 238, 238)',
        colorway=['#2F4077', '#a94645', '#8D533E', '#417DC4'],
        yaxis=dict(
            tickformat=',0f',
            separatethousands=True,
        )
    ),
)

pio.templates.default = "none+gouv"


def format_number(input_number) -> str:
    return "{:,.0f}".format(input_number).replace(",", " ")


def add_callout(text: str, width: int, sm_width: int = 0, number: int = None):
    text_class = 'number-text' if number else 'fr-callout__text'
    number_class = 'callout-number small-number'
    small_width = width * 2 if sm_width == 0 else sm_width
    if number:
        # Below 1M
        if number < 1000000:
            number_class = 'callout-number'
        # Above 10M
        elif number >= 10000000:
            number_class = 'callout-number smaller-number'
        # From 1M to 10M-1
        # don't change initial value

    col = dbc.Col(
        html.Div([
            html.P(format_number(number), className=number_class) if number else None,
            dcc.Markdown(text, className=text_class)
        ],
            className='fr-callout'),
        width=small_width,
        lg=width,
        class_name='flex')
    return col


def add_figure(fig, fig_id: str) -> dbc.Row:
    """
    Boilerplate for figure rows.
    :param fig: a plotly figure
    :param fig_id: if of the figure in the resulting HTML
    :return: HTML Row to be added in a Dash layout
    """

    row = dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            dcc.Graph(id=fig_id, figure=fig, config=extra_config)
                        ],
                        className="fr-callout",
                    )
                ],
                width=12,
            )
        ]
    )
    return row


#
# Établissement
#

df_etablissement: pd.DataFrame = app.data.get_company_data()
print(df_etablissement)
etab = df_etablissement.iloc[0]

#
# BSDDs
#

df_bsdd: pd.DataFrame = app.data.get_bsdd_data()

emis = df_bsdd.query('origine == "émis"')
emis_nb = emis.size
emis_poids = emis['poids'].sum()

recus = df_bsdd.query('origine == "recus"')
recus_poids = recus['poids'].sum()


dash_app.layout = html.Main(
    children=[
        dbc.Container(
            fluid=True,
            id='layout-container',
            children=[
                dbc.Row([
                    html.H1(etab['name']),
                ]),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.P(f'le {datetime.datetime.strftime(today, "%d %b %Y à %H:%M")}'),
                                html.P(["SIRET : " + etab['siret'],
                                        html.Br(),
                                        "S3IC/GUN : " + etab['codeS3ic']]),
                                html.P(etab['address']),
                                html.P('Données pour la période du ' +
                                       datetime.datetime.strftime(app.time_config.date_n_days_ago, "%d %b %Y")
                                       + ' à aujourd\'hui.', className='bold')
                            ], width=6
                        ),
                        dbc.Col(
                            [
                                html.P('Les données pour cet établissement peuvent être consultées sur Trackdéchets.'),
                                html.P('Elles comprennent les bordereaux de suivi de déchets (BSD) dématérialisés,'
                                       ' mais ne comprennent pas :'),
                                html.Ul([
                                    html.Li('les éventuels BSD papiers non dématérialisés'),
                                    html.Li('les bons d\'enlèvement (huiles usagées, pneus)'),
                                    html.Li('les annexes 1 (petites quantités)')
                                ])
                            ], width=6
                        )
                    ]
                ),
                dbc.Row([
                    html.H2('Données des bordereaux de suivi dématérialisés issues de Trackdéchets')
                ]),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='mois_quantités', figure=app.figures.dechets_recus_emis_mois, config=extra_config)
                    ], width=12, lg=6),
                    dbc.Col([
                        html.H4('BSD dangereux sur la période'),
                        html.P([
                            'Poids émis : ' + format_number(emis_poids) + ' t',
                            html.Br(),
                            'Poids reçu : ' + format_number(recus_poids) + ' t'])
                    ], width=12, lg=6),
                ])
            ],
        )
    ]
)



