import logging
from datetime import datetime, timezone

import dash_bootstrap_components as dbc
import pandas as pd
from dash_extensions.enrich import (
    ALL,
    Input,
    Output,
    State,
    callback,
    callback_context,
    dcc,
    exceptions,
    html,
    no_update,
    ServersideOutput,
)

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
                                        html.Div(id="bs-components"),
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
                                ),
                                html.Div(
                                    [
                                        html.H2(
                                            "Donnée installation classée pour la protection de l'Environnement (ICPE)",
                                        ),
                                        html.Div(
                                            (
                                                "Les données ICPE proviennent de la base Géorisque. "
                                                "Ces données ne sont pas à jour et synchronisées pour le moment faute de lien entre Trackdéchets et Géorisque."
                                            ),
                                            className="fr-text--lg",
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
        ServersideOutput("company-data", "data"),
        ServersideOutput("receipt-agrement-data", "data"),
        ServersideOutput("icpe-data", "data"),
        ServersideOutput("bsdd-data", "data"),
        ServersideOutput("bsda-data", "data"),
        ServersideOutput("bsff-data", "data"),
        ServersideOutput("bsdasri-data", "data"),
        ServersideOutput("bsvhu-data", "data"),
        ServersideOutput("additional-data", "data"),
        Output("alert-container", "children"),
        Output("main-layout-fiche", "style"),
    ],
    inputs=[Input("submit-siret", "n_clicks"), State("siret", "value")],
)
def get_data_for_siret(n_clicks: int, siret: str):

    if n_clicks is not None:

        res = []
        if siret is None or len(siret) != 14 or (not siret.isdigit()):
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
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
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                dbc.Alert(
                    "Pas d'entreprise inscrite sur Trackdechets avec ce SIRET.",
                    color="danger",
                ),
                {"display": "none"},
            )

        res.append(company_data_df.iloc[0])

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
                    receipts_agreements_data[config["name"]] = data

        res.append(receipts_agreements_data)

        icpe_data = make_query(
            "get_icpe_data",
            engine="dwh",
            date_columns=["date_debut_exploitation", "date_fin_validite"],
            siret=siret,
            # dtypes={"alinea": str, "rubrique": str},
        )

        if len(icpe_data):
            res.append(icpe_data)
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
                ] = quantity_outliers

            bs_data_df, date_outliers = get_outliers_datetimes_df(
                bs_data_df, date_columns=["sentAt", "receivedAt", "processedAt"]
            )

            if len(date_outliers) > 0:
                additional_data["date_outliers"][bs_config["bs_type"]] = date_outliers

            if len(bs_data_df) != 0:

                to_store["bs_data"] = bs_data_df
                if bs_config.get("bs_revised_data") is not None:
                    bs_revised_data_df = make_query(
                        bs_config["bs_revised_data"],
                        date_columns=["createdAt"],
                        company_id=company_data_df["id"],
                    )
                    if len(bs_revised_data_df) > 0:
                        to_store["bs_revised_data"] = bs_revised_data_df

                res.append(to_store)
            else:
                res.append(None)

        res.append(additional_data)
        return res + [None, {"display": "revert"}]
    else:
        raise exceptions.PreventUpdate


@callback(
    Output("company-name", "children"),
    Input("company-data", "data"),
)
def populate_company_header(company_data: str):

    company_name = company_data["name"]
    today_date = datetime.utcnow().replace(tzinfo=timezone.utc).strftime(r"%d/%m/%Y")

    layout = html.H1(f"{company_name} - {today_date}")
    return layout


@callback(
    Output("company-infos", "children"),
    Input("company-data", "data"),
    Input("receipt-agrement-data", "data"),
)
def populate_company_details(company_data: str, receipt_agrement_data: str):

    layouts = create_company_infos(company_data, receipt_agrement_data)

    return layouts


@callback(
    output=(Output("bs-components", "children"),),
    inputs=(
        Input("company-data", "data"),
        Input("bsdd-data", "data"),
        Input("bsda-data", "data"),
        Input("bsff-data", "data"),
        Input("bsdasri-data", "data"),
        Input("bsvhu-data", "data"),
    ),
)
def populate_bs_components(
    company_data: str,
    bsdd_data: pd.DataFrame,
    bsda_data: pd.DataFrame,
    bsff_data: pd.DataFrame,
    bsdasri_data: pd.DataFrame,
    bsvhu_data: pd.DataFrame,
):

    configs = [
        {
            "data": bsdd_data,
            "name": "BSDD",
            "components_titles": [
                "BSD Dangereux émis et corrigés",
                "Quantité de déchets dangereux en tonnes",
                "BSD dangereux sur l'année",
            ],
            "components_ids": ["bsdd-created-rectified", "bsdd-stock", "bsdd-stats"],
        },
        {
            "data": bsda_data,
            "name": "BSDA",
            "components_titles": [
                "BSD Amiante émis et corrigés",
                "Quantité de déchets amiante en tonnes",
                "BSD d'amiante sur l'année",
            ],
            "components_ids": ["bsda-created-rectified", "bsda-stock", "bsda-stats"],
        },
        {
            "data": bsff_data,
            "name": "BSFF",
            "components_titles": [
                "BS Fluides Frigo émis et corrigés",
                "Quantité de déchets fluides frigo en tonnes",
                "BS Fluides Frigo sur l'année",
            ],
            "components_ids": ["bsff-created-rectified", "bsff-stock", "bsff-stats"],
        },
        {
            "data": bsdasri_data,
            "name": "BSDASRI",
            "components_titles": [
                "BS DASRI émis et corrigés",
                "Quantité de DASRI en tonnes",
                "BS DASRI sur l'année",
            ],
            "components_ids": [
                "bsdasri-created-rectified",
                "bsdasri-stock",
                "bsdasri-stats",
            ],
        },
        {
            "data": bsff_data,
            "name": "BSFF",
            "components_titles": [
                "BS VHU émis et corrigés",
                "Quantité de VHU en tonnes",
                "BS VHU sur l'année",
            ],
            "components_ids": ["bsvhu-created-rectified", "bsvhu-stock", "bsvhu-stats"],
        },
    ]

    layouts = []
    bs_without_data = []
    for config in configs:

        if config["data"] is None:
            bs_without_data.append(config["name"])
            continue

        layouts.extend(
            create_bs_components_layouts(
                config["data"],
                company_data,
                config["components_titles"],
                config["components_ids"],
            )
        )

    return layouts


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
    output=[Output("icpe-section", "children"), Output("icpe-no-data", "style")],
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

            df = pd.concat([v for v in date_outliers.values()])

        return dcc.send_data_frame(
            df.to_csv, f"{bsdd_type}_donnees_aberrantes.csv", index=False
        )
    else:
        raise exceptions.PreventUpdate


@callback(
    output=Output("bs-no-data", "style"),
    inputs=(Input("bs-components", "children"),),
)
def manage_bs_no_data_message(bs_components):
    if bs_components is None:
        return no_update

    if len(bs_components) > 0:
        return {"display": "none"}
    else:
        return {"display": "block"}
