from gc import callbacks
import json
import os
from turtle import width

import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback
import pandas as pd
from app.data.data_extract import make_query

from app.layout.figures_factory import get_bsdd_created_and_revised_figure


def get_layout() -> html.Main:
    layout = html.Main(
        children=[
            dbc.Container(
                fluid=True,
                id="layout-container",
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("SIRET", htmlFor="siret"),
                                    dcc.Input(
                                        os.environ["DEFAULT_SIRET"],
                                        id="siret",
                                        type="text",
                                        minLength=14,
                                        maxLength=14,
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dcc.Markdown(
                                        """
                                    Pour créer un fichier PDF :
                                    
                                    1. Pressez Ctrl + P pour afficher le menu d'impression
                                    2. Dans le menu de choix de l'imprimante, sélectionnez "Sauvegarder au format PDF" 
                                    4. Cliquez sur "Plus de paramètres"
                                    5. Configurez l'échelle d'impression à 60
                                    4. Si possible, choisissez d'exclure les en-têtes et pieds de page
                                    5. Validez l'impression et choisissez l'emplacement et le nom du fichier PDF
                                    """
                                    )
                                ],
                                width=6,
                            ),
                        ],
                        className="no_print",
                    ),
                    dbc.Row(
                        [
                            html.H1(id="company_name"),
                        ]
                    ),
                    dbc.Row(id="company_details"),
                    dbc.Row(
                        [
                            html.H2(
                                "Données des bordereaux de suivi dématérialisés issues de Trackdéchets"
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [],
                                id="bsdd-created-rectified",
                                width=3,
                            )
                        ],
                        id="bsdd-figures",
                    ),
                    dbc.Row([], id="bsdd_graphiques_col"),
                    dbc.Row(
                        [
                            # Stats générales sur les BSDDs
                            dbc.Col([], width=12, lg=6, id="bsdd_summary"),
                            dbc.Col(
                                [], width=6, lg=6, id="poids_departement_recus_col"
                            ),
                        ]
                    ),
                    dbc.Row([], id="bsdd_graphiques_row_2"),
                ],
            ),
            dcc.Store(id="query-result"),
            dcc.Store(id="company-data"),
        ]
    )
    return layout


@callback(Output("company-data", "data"), Input("siret", "value"))
def get_company_data(siret: str):

    if siret is None or len(siret) != 14:
        raise TypeError("Siret is not valid.")

    company_data_df = make_query("get_company_data", siret=siret)

    return company_data_df.iloc[0].to_json()


@callback(
    Output("bsdd-created-rectified", "children"),
    Input("siret", "value"),
    Input("company-data", "data"),
)
def create_bsdd_figures(siret: str, company_data: str):

    if siret is None or len(siret) != 14:
        raise TypeError("Siret is not valid.")

    bsdd_data = make_query("get_bsdd_data", date_columns=["createdAt"], siret=siret)

    company_data = json.loads(company_data)

    bsdd_revised_data = make_query(
        "get_bsdd_revised_data",
        date_columns=["createdAt"],
        company_id=company_data["id"],
    )

    bsdd_created_revised_figure = dcc.Graph(
        figure=get_bsdd_created_and_revised_figure(bsdd_data, bsdd_revised_data, siret)
    )

    return bsdd_created_revised_figure
