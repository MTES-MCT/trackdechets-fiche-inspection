import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import dash_bootstrap_components as dbc
import pandas as pd
from dash import (
    ALL,
    Input,
    Output,
    State,
    callback,
    callback_context,
    dcc,
    html,
    no_update,
)
from dash.exceptions import PreventUpdate

from app.data.data_extract import make_query
from app.data.utils import get_outliers_datetimes_df, get_quantity_outliers
from app.layout.components_factory import (
    create_bs_components_layouts,
    create_company_infos,
    create_complementary_figure_components,
    create_icpe_components,
    create_onsite_waste_components,
    create_waste_input_output_table_component,
)

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
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                "Entrez un SIRET :",
                                                htmlFor="siret",
                                                className="fr-label",
                                            ),
                                            dcc.Input(
                                                id="siret",
                                                type="text",
                                                minLength=14,
                                                maxLength=14,
                                                autoComplete="true",
                                                className="fr-input",
                                            ),
                                            html.Button(
                                                "Générer",
                                                id="submit-siret",
                                                className="fr-btn",
                                            ),
                                            html.Button(
                                                "Imprimer la fiche",
                                                id="print-button",
                                                disabled=True,
                                                className="fr-btn fr-btn--secondary",
                                            ),
                                        ],
                                        id="siret-input-container",
                                    ),
                                    html.Div(id="alert-container"),
                                ],
                                className="no_print",
                                id="form-container",
                            ),
                        ],
                    ),
                    dcc.Loading(
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(id="company-name", width=12),
                                    ]
                                ),
                                html.Div(id="company-infos"),
                                html.Div(
                                    [
                                        html.H2(
                                            "Données des bordereaux de suivi dématérialisés issues de Trackdéchets"
                                        ),
                                        html.Div(
                                            "PAS DE DONNÉES POUR CET ÉTABLISSEMENT",
                                            id="bs-no-data",
                                            className="fr-text--lead no-data-message",
                                        ),
                                        html.Div(id="bsdd-figures"),
                                        html.Div(id="bsda-figures"),
                                        html.Div(id="bsff-figures"),
                                        html.Div(id="bsdasri-figures"),
                                        html.Div(id="bsvhu-figures"),
                                        html.Div(id="complementary-figures"),
                                    ],
                                    id="bordereaux-data-section",
                                ),
                                html.Div(
                                    [
                                        html.H2(
                                            "Déchets sur site (théorique)",
                                        ),
                                        html.Div(
                                            "PAS DE DONNÉES POUR CET ÉTABLISSEMENT",
                                            id="stock-no-data",
                                            className="fr-text--lead no-data-message",
                                        ),
                                        html.Div(id="stock-data-figures"),
                                    ],
                                    id="stock-data-section",
                                    className="page-break",
                                ),
                                html.Div(
                                    [
                                        html.H2(
                                            "Donnée installation classée pour la protection de l'Environnement (ICPE)",
                                            className="page-break",
                                        ),
                                        html.Div(
                                            "PAS DE DONNÉES POUR CET ÉTABLISSEMENT",
                                            id="icpe-no-data",
                                            className="fr-text--lead no-data-message",
                                        ),
                                        html.Div(id="icpe-section"),
                                    ],
                                    id="icpe",
                                ),
                                html.Div(
                                    [
                                        html.H2(
                                            "Liste des déchets entrants/sortants",
                                            className="page-break",
                                        ),
                                        html.Div(
                                            "PAS DE DONNÉES POUR CET ÉTABLISSEMENT",
                                            id="input-output-no-data",
                                            className="fr-text--lead no-data-message",
                                        ),
                                        html.Div(id="input-output-waste-data-table"),
                                    ],
                                    id="input-output-waste",
                                ),
                            ],
                            id="main-layout-fiche",
                            style={"display": "none"},
                        ),
                        type="circle",
                        style={"position": "absolute", "top": "25px"},
                        color="rgb(0, 0, 145)",
                    ),
                ],
            ),
            dcc.Store(id="company-data"),
            dcc.Store(id="receipt-agrement-data"),
            dcc.Store(id="icpe-data"),
            dcc.Store(id="bsdd-data"),
            dcc.Store(id="bsda-data"),
            dcc.Store(id="bsff-data"),
            dcc.Store(id="bsdasri-data"),
            dcc.Store(id="bsvhu-data"),
            dcc.Store(id="additional-data"),
            dcc.Download(id="download-df-csv"),
        ]
    )
    return layout


@callback(
    output=[
        (
            Output("company-data", "data"),
            Output("receipt-agrement-data", "data"),
            Output("icpe-data", "data"),
            Output("bsdd-data", "data"),
            Output("bsda-data", "data"),
            Output("bsff-data", "data"),
            Output("bsdasri-data", "data"),
            Output("bsvhu-data", "data"),
            Output("additional-data", "data"),
        ),
        Output("alert-container", "children"),
        Output("main-layout-fiche", "style"),
    ],
    inputs=[Input("submit-siret", "n_clicks"), State("siret", "value")],
    background=True,
)
def get_data_for_siret(n_clicks: int, siret: str):

    if n_clicks is not None:

        res = []
        if siret is None or len(siret) != 14:
            return (
                (no_update,) * 9,
                dbc.Alert(
                    "SIRET non conforme",
                    color="danger",
                ),
                {"display": "none"},
            )

        company_data_df = make_query(
            "get_company_data", siret=siret, date_columns=["createdAt"]
        )

        if len(company_data_df) == 0:

            return (
                (no_update,) * 9,
                dbc.Alert(
                    "Aucune entreprise avec ce SIRET inscrite sur Trackdéchets",
                    color="danger",
                ),
                {"display": "none"},
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

        icpe_data = make_query(
            "get_icpe_data",
            engine="dwh",
            date_columns=["date_debut_exploitation", "date_fin_validite"],
            siret=siret,
            # dtypes={"alinea": str, "rubrique": str},
        )

        if len(icpe_data):
            res.append(icpe_data.to_json(date_format="iso"))
        else:
            res.append(None)

        bs_dtypes = {
            "id": str,
            "createdAt": str,
            "sentAt": str,
            "receivedAt": str,
            "processedAt": str,
            "emitterCompanySiret": str,
            "emitterCompanyAddress": str,
            "recipientCompanySiret": str,
            "wasteDetailsQuantity": float,
            "quantityReceived": float,
            "wasteCode": str,
            "status": str,
        }

        bs_configs = [
            {
                "bs_type": "BSDD",
                "bs_data": "get_bsdd_data",
                "bs_revised_data": "get_bsdd_revised_data",
            },
            {
                "bs_type": "BSDA",
                "bs_data": "get_bsda_data",
                "bs_revised_data": "get_bsda_revised_data",
            },
            {"bs_type": "BSFF", "bs_data": "get_bsff_data"},
            {"bs_type": "BSDASRI", "bs_data": "get_bsdasri_data"},
            {"bs_type": "BSVHU", "bs_data": "get_bsvhu_data"},
        ]

        additional_data = {"date_outliers": {}, "quantity_outliers": {}}

        for bs_config in bs_configs:

            to_store = {"bs_data": None, "bs_revised_data": None}

            bs_data_df = make_query(
                bs_config["bs_data"],
                dtypes=bs_dtypes,
                siret=siret,
            )

            quantity_outliers = get_quantity_outliers(bs_data_df, bs_config["bs_type"])

            if len(quantity_outliers) > 0:
                additional_data["quantity_outliers"][
                    bs_config["bs_type"]
                ] = quantity_outliers.to_json()

            bs_data_df, date_outliers = get_outliers_datetimes_df(
                bs_data_df, date_columns=["sentAt", "receivedAt", "processedAt"]
            )

            if len(date_outliers) > 0:
                additional_data["date_outliers"][bs_config["bs_type"]] = date_outliers

            if len(bs_data_df) != 0:

                to_store["bs_data"] = bs_data_df.to_json()
                if bs_config.get("bs_revised_data") is not None:
                    bs_revised_data_df = make_query(
                        bs_config["bs_revised_data"],
                        date_columns=["createdAt"],
                        company_id=company_data_df["id"],
                    )
                    if len(bs_revised_data_df) > 0:
                        to_store["bs_revised_data"] = bs_revised_data_df.to_json()

                res.append(to_store)
            else:
                res.append(None)

        res.append(additional_data)
        return tuple(res), None, {"display": "revert"}
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
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
    ),
)
def populate_bsdd_components(company_data: str, bsdd_data: str):

    if bsdd_data is None:
        logger.info("Pas de données BSDD trouvées pour le siret")
        return [html.Div()]

    layout = create_bs_components_layouts(
        bsdd_data,
        company_data,
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

    if bsda_data is None or len(bsda_data) == 0:
        logger.info("Pas de données BSDA trouvées pour le siret")
        return [html.Div()]

    layout = create_bs_components_layouts(
        bsda_data,
        company_data,
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

    if bsff_data is None or len(bsff_data) == 0:
        logger.info("Pas de données BSDFF trouvées pour le siret")
        return [html.Div()]

    layout = create_bs_components_layouts(
        bsff_data,
        company_data,
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

    if bsdasri_data is None:
        logger.info("Pas de données BSDASRI trouvées pour le siret")
        return [html.Div()]

    layout = create_bs_components_layouts(
        bsdasri_data,
        company_data,
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

    if bsvhu_data is None:
        logger.info("Pas de données BSDA trouvées pour le siret")
        return [html.Div()]

    layout = create_bs_components_layouts(
        bsvhu_data,
        company_data,
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
        Input("additional-data", "data"),
    ),
)
def populate_complementary_figures_section(*args):
    layout = create_complementary_figure_components(*args)
    return layout


@callback(
    output=(Output("stock-data-figures", "children"), Output("stock-no-data", "style")),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_onsite_waste_section(*args):
    layout = create_onsite_waste_components(*args)

    return layout


@callback(
    output=(
        Output("input-output-waste-data-table", "children"),
        Output("input-output-no-data", "style"),
    ),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_waste_input_output_table(*args):
    layout = create_waste_input_output_table_component(*args)

    return layout


@callback(
    output=(Output("icpe-section", "children"), Output("icpe-no-data", "style")),
    inputs=(
        Input("company-data", "data"),
        Input("icpe-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_icpe_section(*args):
    layout = create_icpe_components(*args)

    return layout


@callback(
    Output("download-df-csv", "data"),
    Input({"type": "download-date-outliers", "index": ALL}, "n_clicks"),
    State("additional-data", "data"),
    prevent_initial_call=True,
)
def handle_download_outliers_data(nclicks, additional_data):

    if any(e is not None for e in nclicks):
        trigger = list(callback_context.triggered_prop_ids.values())[0]
        download_request = trigger["type"]
        bsdd_type = trigger["index"]
        if download_request == "download-date-outliers":
            date_outliers = additional_data["date_outliers"][bsdd_type]

            df = pd.concat([pd.read_json(v) for v in date_outliers.values()])

        return dcc.send_data_frame(
            df.to_csv, f"{bsdd_type}_donnees_aberrantes.csv", index=False
        )
    else:
        raise PreventUpdate


@callback(
    output=Output("bs-no-data", "style"),
    inputs=(
        Input("bsdd-figures", "children"),
        Input("bsda-figures", "children"),
        Input("bsff-figures", "children"),
        Input("bsvhu-figures", "children"),
        Input("bsdasri-figures", "children"),
        Input("complementary-figures", "children"),
    ),
)
def manage_bs_no_data_message(*args):
    if all(arg is None for arg in args):
        return no_update

    for e in args:
        if isinstance(e, list):
            if e[0]["props"]["children"] is not None:
                return {"display": "none"}
            else:
                return {"display": "block"}
        else:
            if isinstance(e["props"]["children"], list) and (
                len(e["props"]["children"]) != 0
            ):
                return {"display": "none"}
            elif e["props"]["children"] is not None:
                return {"display": "none"}
            else:
                return {"display": "block"}
