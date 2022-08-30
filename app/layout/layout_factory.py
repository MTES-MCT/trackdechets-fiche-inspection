import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import dash_bootstrap_components as dbc
import pandas as pd
from app.data.data_extract import (
    load_and_preprocess_regions_geographical_data,
    load_departements_regions_data,
    make_query,
)
from app.layout.components.figure_component import (
    BSRefusalsComponent,
    WasteOriginsComponent,
    WasteOriginsMapComponent,
)
from app.layout.components_factory import (
    create_bs_components_layouts,
    create_bs_refusal_component,
    create_company_infos,
    create_onsite_waste_components,
)
from dash import Input, Output, State, callback, dcc, html, no_update
from dash.exceptions import PreventUpdate

from .components.company_component import CompanyComponent
from .components.stats_component import StorageStatsComponent

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
                                        name="siret",
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
                            dbc.Col(id="company-name", width=12),
                        ]
                    ),
                    html.Div(id="company-infos"),
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    html.H2(
                                        "Données des bordereaux de suivi dématérialisés issues de Trackdéchets"
                                    )
                                ]
                            ),
                            html.Div(
                                id="bsdd-figures",
                            ),
                            html.Div(
                                id="bsda-figures",
                            ),
                            html.Div(
                                id="bsff-figures",
                            ),
                            html.Div(
                                id="bsdasri-figures",
                            ),
                            html.Div(
                                id="bsvhu-figures",
                            ),
                            html.Div(
                                [],
                                id="complementary-figures",
                            ),
                        ],
                        id="bordereaux-data-section",
                    ),
                    html.Div(
                        [
                            dbc.Row([html.H2("Déchets sur site (théorique)")]),
                            html.Div(id="stock-data-figures"),
                        ],
                        id="stock-data-section",
                    ),
                ],
            ),
            dcc.Store(id="company-data"),
            dcc.Store(id="receipt-agrement-data"),
            dcc.Store(id="bsdd-data"),
            dcc.Store(id="bsda-data"),
            dcc.Store(id="bsff-data"),
            dcc.Store(id="bsdasri-data"),
            dcc.Store(id="bsvhu-data"),
        ]
    )
    return layout


@callback(
    output=[
        (
            Output("company-data", "data"),
            Output("receipt-agrement-data", "data"),
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
def get_data_for_siret(n_clicks: int, siret: str):

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

        receipts_agreements_data = {}
        for config in [
            {
                "name": "Récépissé Transporteur",
                "column": "transporterReceiptId",
                "sql_file": "get_transporterReceiptId_data",
            },
            {
                "name": "Récépissé Négociant",
                "column": "traderReceiptId",
                "sql_file": "get_traderReceiptId_data",
            },
            {
                "name": "Récépissé Courtier",
                "column": "brokerReceiptId",
                "sql_file": "get_brokerReceiptId_data",
            },
            {
                "name": "Agrément Démolisseur ",
                "column": "vhuAgrementDemolisseurId",
                "sql_file": "get_vhuAgrement_data",
            },
            {
                "name": "Agrément Broyeur",
                "column": "vhuAgrementBroyeurId",
                "sql_file": "get_vhuAgrement_data",
            },
        ]:
            id_ = company_data_df[config["column"]].item()
            if id_ is not None:
                data = make_query(
                    config["sql_file"],
                    date_columns=["validityLimit"],
                    id=id_,
                )
                if len(data) != 0:
                    receipts_agreements_data[config["name"]] = data.to_json()

        res.append(receipts_agreements_data)

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
    Output("company-name", "children"),
    Input("company-data", "data"),
)
def populate_company_header(company_data: str):
    company_data = json.loads(company_data)
    company_name = company_data["name"]
    today_date = datetime.now(tz=ZoneInfo("Europe/Paris")).strftime(r"%d/%m/%Y")

    layout = html.H1(f"{company_name} - {today_date}")
    return layout


@callback(
    Output("company-infos", "children"),
    Input("company-data", "data"),
    Input("receipt-agrement-data", "data"),
)
def populate_company_details(company_data: str, receipt_agrement_data: str):
    company_data = json.loads(company_data)
    receipt_agrement_data = {
        k: pd.read_json(v, convert_dates=["validityLimit"])
        for k, v in receipt_agrement_data.items()
    }

    layouts = create_company_infos(company_data, receipt_agrement_data)

    return layouts


@callback(
    output=(Output("bsdd-figures", "children"),),
    inputs=(Input("company-data", "data"), Input("bsdd-data", "data")),
)
def populate_bsdd_components(company_data: str, bsdd_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsdd_data is None or len(bsdd_data) == 0:
        logger.info("Pas de données trouvées pour le siret %s", siret)
        return no_update

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

    layout = create_bs_components_layouts(
        bsdd_data_df,
        bsdd_revised_data_df,
        siret,
        [
            "BSD Dangereux émis et corrigés",
            "Quantité de déchets dangereux en tonnes",
            "BSD dangereux sur l'année",
        ],
        ["bsdd-created-rectified", "bsdd-stock", "bsdd-stats"],
    )

    return layout


@callback(
    output=Output("bsda-figures", "children"),
    inputs=(Input("company-data", "data"), Input("bsda-data", "data")),
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

    layout = create_bs_components_layouts(
        bsda_data_df,
        bsda_revised_data_df,
        siret,
        [
            "BSD Amiante émis et corrigés",
            "Quantité de déchets amiante en tonnes",
            "BSD d'amiante sur l'année",
        ],
        ["bsda-created-rectified", "bsda-stock", "bsda-stats"],
    )

    return layout


@callback(
    output=Output("bsff-figures", "children"),
    inputs=[Input("company-data", "data"), Input("bsff-data", "data")],
)
def populate_bsff_components(company_data: str, bsff_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsff_data is None or len(bsff_data) == 0:
        logger.info("Pas de données BSDFF trouvées pour le siret %s", siret)
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

    layout = create_bs_components_layouts(
        bsff_data_df,
        None,
        siret,
        [
            "BS Fluides Frigo émis et corrigés",
            "Quantité de déchets fluides frigo en tonnes",
            "BS Fluides Frigo sur l'année",
        ],
        ["bsda-created-rectified", "bsda-stock", "bsda-stats"],
    )

    return layout


@callback(
    output=Output("bsdasri-figures", "children"),
    inputs=(Input("company-data", "data"), Input("bsdasri-data", "data")),
)
def populate_bsdasri_components(company_data: str, bsdasri_data: str):

    company_data = json.loads(company_data)
    siret = company_data["siret"]

    if bsdasri_data is None or len(bsdasri_data) == 0:
        logger.info("Pas de données BSDASRI trouvées pour le siret %s", siret)
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

    layout = create_bs_components_layouts(
        bsdasri_data_df,
        None,
        siret,
        [
            "BS DASRI émis et corrigés",
            "Quantité de DASRI en tonnes",
            "BS DASRI sur l'année",
        ],
        ["bsdasri-created-rectified", "bsdasri-stock", "bsdasri-stats"],
    )

    return layout


@callback(
    output=Output("bsvhu-figures", "children"),
    inputs=(Input("company-data", "data"), Input("bsvhu-data", "data")),
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

    layout = create_bs_components_layouts(
        bsvhu_data_df,
        None,
        siret,
        [
            "BS VHU émis et corrigés",
            "Quantité de VHU en tonnes",
            "BS VHU sur l'année",
        ],
        ["bsvhu-created-rectified", "bsvhu-stock", "bsvhu-stats"],
    )

    return layout


@callback(
    output=(Output("complementary-figures", "children")),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_complementary_figures_components(*args):
    layout = create_bs_refusal_component(*args)
    return layout


@callback(
    output=(Output("stock-data-figures", "children"),),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_onsite_waste_components(*args):
    layout = create_onsite_waste_components(*args)

    return layout
