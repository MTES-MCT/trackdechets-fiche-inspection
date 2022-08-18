from datetime import datetime, timedelta, tzinfo
import json
import logging
from zoneinfo import ZoneInfo

import dash_bootstrap_components as dbc
import pandas as pd

from app.data.data_extract import load_departements_data, make_query
from dash import Input, Output, State, callback, dcc, html, no_update
from dash.exceptions import PreventUpdate

from .components.stats_component import StorageStatsComponent
from .components.company_component import CompanyComponent
from app.layout.components.figure_component import (
    BSRefusalsComponent,
    WasteOrigineComponent,
)
from app.layout.components_factory import create_bs_components_layouts

logger = logging.getLogger()

DEPARTEMENTS_DATA = load_departements_data()


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
                                width=12,
                            ),
                        ],
                        className="no_print",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(id="company_name", width=12),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(id="company-details", width=6),
                            dbc.Col(
                                dcc.Markdown(
                                    """
Les données pour cet établissement peuvent être consultées sur Trackdéchets.

Elles comprennent les bordereaux de suivi de déchets (BSD) dématérialisés, mais ne comprennent pas :
- les éventuels BSD papiers non dématérialisés,
- les bons d’enlèvements (huiles usagées et pneus)
- les annexes 1 (petites quantités)""",
                                    style={"display": "None"},
                                    id="general-infos",
                                ),
                                width=6,
                            ),
                        ]
                    ),
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
                            dbc.Col(
                                [],
                                id="bsff-created-rectified",
                                width=3,
                            ),
                            dbc.Col(
                                [],
                                id="bsff-stock",
                                width=3,
                            ),
                            dbc.Col([], id="bsff-stats", width=3),
                        ],
                        id="bsff-figures",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [],
                                id="bsdasri-created-rectified",
                                width=3,
                            ),
                            dbc.Col(
                                [],
                                id="bsdasri-stock",
                                width=3,
                            ),
                            dbc.Col([], id="bsdasri-stats", width=3),
                        ],
                        id="bsdasri-figures",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [],
                                id="bsvhu-created-rectified",
                                width=3,
                            ),
                            dbc.Col(
                                [],
                                id="bsvhu-stock",
                                width=3,
                            ),
                            dbc.Col([], id="bsvhu-stats", width=3),
                        ],
                        id="bsvhu-figures",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(id="bs-refusal", width=3),
                            dbc.Col(id="complementary-info", width=3),
                        ]
                    ),
                    dbc.Row([html.H2("Déchets sur site (théorique)")]),
                    dbc.Row(
                        [
                            dbc.Col(width=3, id="waste-stock"),
                            dbc.Col(width=3, id="waste-origins"),
                        ]
                    ),
                ],
            ),
            dcc.Store(id="company-data"),
            dcc.Store(id="bsdd-data"),
            dcc.Store(id="bsda-data"),
            dcc.Store(id="bsff-data"),
            dcc.Store(id="bsdasri-data"),
            dcc.Store(id="bsvhu-data"),
            dcc.Store(id="departements-data"),
        ]
    )
    return layout


@callback(
    output=[
        (
            Output("company-data", "data"),
            Output("bsdd-data", "data"),
            Output("bsda-data", "data"),
            Output("bsff-data", "data"),
            Output("bsdasri-data", "data"),
            Output("bsvhu-data", "data"),
        ),
        Output("alert-container", "children"),
    ],
    inputs=[Input("submit-siret", "n_clicks"), State("siret", "value")],
)
def get_company_data(n_clicks: int, siret: str):

    if n_clicks is not None:

        res = []
        if siret is None or len(siret) != 14:
            return (
                (no_update,) * 6,
                dbc.Alert(
                    "SIRET non conforme",
                    color="danger",
                ),
            )

        company_data_df = make_query("get_company_data", siret=siret)

        if len(company_data_df) == 0:

            return (
                (no_update,) * 6,
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
            {"bsff_data_df": "get_bsff_data"},
            {"bsdasri_data_df": "get_bsdasri_data"},
            {"bsvhu_data_df": "get_bsvhu_data"},
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
        return tuple(res), None
    else:
        raise PreventUpdate


@callback(
    Output("company_name", "children"),
    Output("general-infos", "style"),
    Input("company-data", "data"),
)
def populate_company_header(company_data: str):
    company_data = json.loads(company_data)
    company_name = company_data["name"]
    today_date = datetime.now(tz=ZoneInfo("Europe/Paris")).strftime("%d %B %Y")

    layout = html.H1(f"{company_name} - {today_date}")
    return layout, {"display": "block"}


@callback(
    Output("company-details", "children"),
    Input("company-data", "data"),
)
def populate_company_details(company_data: str):
    company_data = json.loads(company_data)

    company_component = CompanyComponent(company_data=company_data)

    return company_component.create_layout()


@callback(
    Output("bsdd-created-rectified", "children"),
    Output("bsdd-stock", "children"),
    Output("bsdd-stats", "children"),
    Input("company-data", "data"),
    Input("bsdd-data", "data"),
)
def populate_bsdd_components(company_data: str, bsdd_data: str):

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

    outputs = create_bs_components_layouts(
        bsdd_data_df,
        bsdd_revised_data_df,
        siret,
        [
            "BSD Dangereux émis et corrigés",
            "Quantité de déchets dangereux en tonnes",
            "BSD dangereux sur l'année",
        ],
    )

    return outputs


@callback(
    Output("bsda-created-rectified", "children"),
    Output("bsda-stock", "children"),
    Output("bsda-stats", "children"),
    Input("company-data", "data"),
    Input("bsda-data", "data"),
)
def populate_bsda_components(company_data: str, bsda_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsda_data is None or len(bsda_data) == 0:
        logger.info("Pas de données BSDA trouvées pour le siret %s", siret)
        return [], [], []

    bsda_data_df = pd.read_json(
        bsda_data["bsda_data_df"],
        dtype={
            "emitterCompanySiret": str,
            "recipientCompanySiret": str,
            "wasteDetailsQuantity": float,
            "quantityReceived": float,
        },
        convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
    )

    if bsda_data["bsda_revised_data_df"] is not None:
        bsda_revised_data_df = pd.read_json(
            bsda_data["bsda_revised_data_df"], convert_dates=["createdAt"]
        )
    else:
        bsda_revised_data_df = None

    outputs = create_bs_components_layouts(
        bsda_data_df,
        bsda_revised_data_df,
        siret,
        [
            "BSD Amiante émis et corrigés",
            "Quantité de déchets amiante en tonnes",
            "BSD d'amiante sur l'année",
        ],
    )

    return outputs


@callback(
    Output("bsff-created-rectified", "children"),
    Output("bsff-stock", "children"),
    Output("bsff-stats", "children"),
    Input("company-data", "data"),
    Input("bsff-data", "data"),
)
def populate_bsff_components(company_data: str, bsff_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsff_data is None or len(bsff_data) == 0:
        logger.info("Pas de données BSDA trouvées pour le siret %s", siret)
        return [], [], []

    bsff_data_df = pd.read_json(
        bsff_data["bsff_data_df"],
        dtype={
            "emitterCompanySiret": str,
            "recipientCompanySiret": str,
            "wasteDetailsQuantity": float,
            "quantityReceived": float,
        },
        convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
    )

    outputs = create_bs_components_layouts(
        bsff_data_df,
        None,
        siret,
        [
            "BS Fluides Frigo émis et corrigés",
            "Quantité de déchets fluides frigo en tonnes",
            "BS Fluides Frigo sur l'année",
        ],
    )

    return outputs


@callback(
    Output("bsdasri-created-rectified", "children"),
    Output("bsdasri-stock", "children"),
    Output("bsdasri-stats", "children"),
    Input("company-data", "data"),
    Input("bsdasri-data", "data"),
)
def populate_bsdasri_components(company_data: str, bsdasri_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsdasri_data is None or len(bsdasri_data) == 0:
        logger.info("Pas de données BSDA trouvées pour le siret %s", siret)
        return [], [], []

    bsdasri_data_df = pd.read_json(
        bsdasri_data["bsdasri_data_df"],
        dtype={
            "emitterCompanySiret": str,
            "recipientCompanySiret": str,
            "wasteDetailsQuantity": float,
            "quantityReceived": float,
        },
        convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
    )

    outputs = create_bs_components_layouts(
        bsdasri_data_df,
        None,
        siret,
        [
            "BS DASRI émis et corrigés",
            "Quantité de DASRI en tonnes",
            "BS DASRI sur l'année",
        ],
    )

    return outputs


@callback(
    Output("bsvhu-created-rectified", "children"),
    Output("bsvhu-stock", "children"),
    Output("bsvhu-stats", "children"),
    Input("company-data", "data"),
    Input("bsvhu-data", "data"),
)
def populate_bsvhu_components(company_data: str, bsvhu_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsvhu_data is None or len(bsvhu_data) == 0:
        logger.info("Pas de données BSDA trouvées pour le siret %s", siret)
        return [], [], []

    bsvhu_data_df = pd.read_json(
        bsvhu_data["bsvhu_data_df"],
        dtype={
            "emitterCompanySiret": str,
            "recipientCompanySiret": str,
            "wasteDetailsQuantity": float,
            "quantityReceived": float,
        },
        convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
    )

    outputs = create_bs_components_layouts(
        bsvhu_data_df,
        None,
        siret,
        [
            "BS VHU émis et corrigés",
            "Quantité de VHU en tonnes",
            "BS VHU sur l'année",
        ],
    )

    return outputs


@callback(
    output=(Output("bs-refusal", "children")),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_refusals_figure_component(
    company_data: str,
    bsdd_data: str,
    bsda_data: str,
    bsff_data: str,
    bsdasri_data: str,
    bsvhu_data: str,
):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    dfs = {}
    load_configs = [
        {"name": "Déchets Dangereux", "data": bsdd_data},
        {"name": "Amiante", "data": bsda_data},
        {"name": "Fluides Frigo", "data": bsff_data},
        {"name": "DASRI", "data": bsdasri_data},
        {"name": "VHU", "data": bsvhu_data},
    ]
    for config in load_configs:

        name = config["name"]
        data = config["data"]
        if data is None:
            continue
        data_df = data[list(data.keys())[0]]
        bs_data_df = pd.read_json(
            data_df,
            dtype={
                "emitterCompanySiret": str,
                "recipientCompanySiret": str,
                "wasteDetailsQuantity": float,
                "quantityReceived": float,
            },
            convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
        )
        dfs[name] = bs_data_df

    bs_refusals_component = BSRefusalsComponent(
        component_title=r"BSD refusés en % de BSD émis",
        company_siret=siret,
        bs_data_dfs=dfs,
    )

    return bs_refusals_component.create_layout()


@callback(
    output=(Output("waste-stock", "children"), Output("waste-origins", "children")),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_onsite_waste_components(
    company_data: str,
    bsdd_data: str,
    bsda_data: str,
    bsff_data: str,
    bsdasri_data: str,
    bsvhu_data: str,
):
    company_data = json.loads(company_data)
    siret = company_data["siret"]

    dfs = {}
    load_configs = [
        {"name": "Déchets Dangereux", "data": bsdd_data},
        {"name": "Amiante", "data": bsda_data},
        {"name": "Fluides Frigo", "data": bsff_data},
        {"name": "DASRI", "data": bsdasri_data},
        {"name": "VHU", "data": bsvhu_data},
    ]
    for config in load_configs:

        name = config["name"]
        data = config["data"]
        if data is None:
            continue
        data_df = data[list(data.keys())[0]]
        bs_data_df = pd.read_json(
            data_df,
            dtype={
                "emitterCompanySiret": str,
                "recipientCompanySiret": str,
                "wasteDetailsQuantity": float,
                "quantityReceived": float,
            },
            convert_dates=["createdAt", "sentAt", "receivedAt", "processedAt"],
        )
        dfs[name] = bs_data_df

    storage_stats_component = StorageStatsComponent(
        component_title="Déchets entreposés sur site actuellement",
        company_siret=siret,
        bs_data_dfs=dfs,
    )

    waste_origin_component = WasteOrigineComponent(
        component_title="Origine des déchets",
        company_siret=siret,
        bs_data_dfs=dfs,
        departements_df=DEPARTEMENTS_DATA,
    )

    return (
        storage_stats_component.create_layout(),
        waste_origin_component.create_layout(),
    )
