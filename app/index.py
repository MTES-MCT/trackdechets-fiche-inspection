from dash import html, dcc
import dash_bootstrap_components as dbc
from os import getenv

from app.app import dash_app, extra_config
import app.data
import app.utils
import app.figures


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


# else:
#     graph_rows = [
#         dbc.Row([
#
#         ])
#     ]

dash_app.layout = html.Main(
    children=[
        dbc.Container(
            fluid=True,
            id='layout-container',
            children=[
                dbc.Row([
                    dbc.Col(
                        [
                            html.Label("SIRET", htmlFor='siret'),
                            dcc.Input(getenv('DEFAULT_SIRET'), id='siret', type="text")],
                        width=6
                    ),
                    dbc.Col([
                        dcc.Markdown("""
                                 Pour créer un fichier PDF :
                                 
                                 1. Pressez Ctrl + P pour afficher le menu d'impression
                                 2. Dans le menu de choix de l'imprimante, sélectionnez "Sauvegarder au format PDF" 
                                 4. Cliquez sur "Plus de paramètres"
                                 5. Configurez l'échelle d'impression à 60
                                 4. Si possible, choisissez d'exclure les en-têtes et pieds de page
                                 5. Validez l'impression et choisissez l'emplacement et le nom du fichier PDF
                                 """)
                    ],
                        width=6
                    )
                ], className='no_print'),
                dbc.Row([
                    html.H1(id='company_name'),
                ]),
                dbc.Row(id='company_details'),
                dbc.Row([
                    html.H2('Données des bordereaux de suivi dématérialisés issues de Trackdéchets')
                ]),
                dbc.Row([

                ], id='bsdd_graphiques_col'),
                dbc.Row([
                    # Stats générales sur les BSDDs
                    dbc.Col([], width=12, lg=6, id='bsdd_summary'),
                    dbc.Col([

                    ], width=6, lg=6, id='poids_departement_recus_col')
                ]),
                dbc.Row([


                ], id='bsdd_graphiques_row_2'),
            ]

        ),
        dcc.Store(id='query-result')
    ]
)
