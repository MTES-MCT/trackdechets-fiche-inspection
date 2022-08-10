from datetime import datetime
import json
import logging

import dash_bootstrap_components as dbc
import pandas as pd

from app.data.data_extract import make_query
from dash import Input, Output, State, callback, dcc, html, no_update
from dash.exceptions import PreventUpdate
from app.layout.components_factory import create_bs_components_layouts

logger = logging.getLogger()


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
                                        id="siret",
                                        type="text",
                                        minLength=14,
                                        maxLength=14,
                                        autoComplete="true",
                                    ),
                                    html.Button(
                                        "Générer",
                                        id="submit-siret",
                                    ),
                                    html.Div(id="alert-container"),
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
                            ),
                            dbc.Col(
                                [],
                                id="bsdd-stock",
                                width=3,
                            ),
                            dbc.Col([], id="bsdd-stats", width=3),
                        ],
                        id="bsdd-figures",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [],
                                id="bsda-created-rectified",
                                width=3,
                            ),
                            dbc.Col(
                                [],
                                id="bsda-stock",
                                width=3,
                            ),
                            dbc.Col([], id="bsda-stats", width=3),
                        ],
                        id="bsda-figures",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(id="bsd-refusal", width=3),
                            dbc.Col(id="complementary-info", width=3),
                        ]
                    ),
                ],
            ),
            dcc.Store(id="company-data"),
            dcc.Store(id="bsdd-data"),
            dcc.Store(id="bsda-data"),
        ]
    )
    return layout


@callback(
    output=[
        (
            Output("company-data", "data"),
            Output("bsdd-data", "data"),
            Output("bsda-data", "data"),
        ),
        Output("alert-container", "children"),
    ],
    inputs=[Input("submit-siret", "n_clicks"), State("siret", "value")],
)
def get_company_data(n_clicks: int, siret: str):

    if n_clicks is not None:

        res = []
        if siret is None or len(siret) != 14:
            raise TypeError("Siret is not valid.")

        company_data_df = make_query("get_company_data", siret=siret)

        if len(company_data_df) == 0:

            return (
                no_update,
                dbc.Alert(
                    "Aucune entreprise avec ce SIRET inscrite sur Trackdéchets",
                    color="danger",
                ),
            )

        res.append(company_data_df.iloc[0].to_json())

        bs_configs = [
            {
                "bsdd_data_df": "get_bsdd_data",
                "bsdd_revised_data_df": "get_bsdd_revised_data",
            },
            {
                "bsda_data_df": "get_bsda_data",
                "bsda_revised_data_df": "get_bsda_revised_data",
            },
        ]

        for bs_config in bs_configs:

            keys = list(bs_config.keys())
            queries = list(bs_config.values())

            to_store = {key: None for key in keys}

            bs_data = make_query(
                queries[0],
                date_columns=["createdAt", "sentAt", "receivedAt", "processedAt"],
                siret=siret,
            )

            if len(bs_data) != 0:

                to_store[keys[0]] = bs_data.to_json()
                if len(queries) == 2:
                    bs_revised_data = make_query(
                        queries[1],
                        date_columns=["createdAt"],
                        company_id=company_data_df["id"],
                    )
                    if len(bs_revised_data) > 0:
                        to_store[keys[1]] = bs_revised_data.to_json()

                res.append(to_store)
            else:
                res.append(None)
        print(res)
        return tuple(res), None
    else:
        raise PreventUpdate


@callback(
    Output("bsdd-created-rectified", "children"),
    Output("bsdd-stock", "children"),
    Output("bsdd-stats", "children"),
    Input("company-data", "data"),
    Input("bsdd-data", "data"),
)
def create_bsdd_figures(company_data: str, bsdd_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsdd_data is None or len(bsdd_data) == 0:
        logger.info("Pas de données trouvées pour le siret %s", siret)
        return [], [], []

    bsdd_data_df = pd.read_json(
        bsdd_data["bsdd_data_df"],
        dtype={
            "emitterCompanySiret": str,
            "recipientCompanySiret": str,
            "wasteDetailsQuantity": float,
            "quantityReceived": float,
        },
        convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
    )
    if bsdd_data["bsdd_revised_data_df"] is not None:
        bsdd_revised_data_df = pd.read_json(
            bsdd_data["bsdd_revised_data_df"], dtype=False, convert_dates=["createdAt"]
        )
    else:
        bsdd_revised_data_df = None

    outputs = create_bs_components_layouts(bsdd_data_df, bsdd_revised_data_df, siret)

    return outputs


@callback(
    Output("bsda-created-rectified", "children"),
    Output("bsda-stock", "children"),
    Output("bsda-stats", "children"),
    Input("company-data", "data"),
    Input("bsda-data", "data"),
)
def create_bsda_figures(company_data: str, bsda_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsda_data is None or len(bsda_data) == 0:
        logger.info("Pas de données BSDA trouvées pour le siret %s", siret)
        return [], [], []

    bsda_data_df = pd.read_json(bsda_data["bsda_data_df"])
    if bsda_data["bsda_revised_data_df"] is not None:
        bsda_revised_data_df = pd.read_json(bsda_data["bsda_revised_data_df"])
    else:
        bsda_revised_data_df = None

    outputs = create_bs_components_layouts(bsda_data_df, bsda_revised_data_df, siret)

    return outputs
