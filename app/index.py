import datetime
import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from os import getenv

from app.app import dash_app, extra_config
from app.time_config import time_delta_m, today
import app.data
import app.figures
import app.utils


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
            html.P(app.utils.format_number_str(number), className=number_class) if number else None,
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
etab = df_etablissement.iloc[0]

#
# BSDDs
#

df_bsdd: pd.DataFrame = app.data.get_bsdd_data()

emis_nb = app.data.emis.size
emis_poids = app.data.emis['poids'].sum()

recus_poids = app.data.recus['poids'].sum()

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
                                html.P('Inscrit sur Trackdéchets depuis le '
                                       f'{datetime.datetime.strftime(etab["createdAt"], "%d %b %Y à %H:%M")}'),
                                html.P('Données pour la période du ' +
                                       datetime.datetime.strftime(app.time_config.date_n_days_ago, "%d %b %Y")
                                       + ' à aujourd\'hui (' + getenv("TIME_PERIOD_M") + ' derniers mois).',
                                       className='bold')
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
                        dcc.Graph(id='mois_quantités', figure=app.figures.dechets_recus_emis_poids_mois,
                                  config=extra_config)
                    ], width=6, lg=6),
                    dbc.Col(
                        [
                            dcc.Graph(id='mois_emis', figure=app.figures.bsdd_emis_acceptation_mois,
                                      config=extra_config)
                        ], width=6, lg=6
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H4('BSD dangereux sur la période'),
                        html.P([
                            'Poids émis : ' + app.utils.format_number_str(emis_poids) + ' t',
                            html.Br(),
                            'Poids reçu : ' + app.utils.format_number_str(recus_poids) + ' t',
                            html.Br(),
                            'Stock théorique sur la période : ' + app.utils.format_number_str(recus_poids - emis_poids)
                            + ' t']),

                        html.P([
                            'BSDD émis : ' + app.utils.format_number_str(app.data.emis_nb),
                            html.Br(),
                            'BSDD reçus : ' + app.utils.format_number_str(app.data.recus_nb),
                        ])
                    ], width=12, lg=6),
                    dbc.Col([
                        dcc.Graph(id='poids_departement_recus', figure=app.figures.dechets_recus_poids_departement,
                                  config=extra_config)
                    ], width=6, lg=6)
                ])
            ],
        )
    ]
)
