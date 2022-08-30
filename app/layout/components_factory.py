import json
from typing import List

import dash_bootstrap_components as dbc
import pandas as pd
from app.data.data_extract import (
    load_and_preprocess_regions_geographical_data,
    load_departements_regions_data,
)
from app.layout.components.company_component import (
    CompanyComponent,
    ReceiptAgrementsComponent,
)
from app.layout.components.figure_component import (
    BSCreatedAndRevisedComponent,
    BSRefusalsComponent,
    StockComponent,
    WasteOriginsComponent,
    WasteOriginsMapComponent,
)
from app.layout.components.stats_component import (
    BSStatsComponent,
    StorageStatsComponent,
)
from dash import no_update, dcc

DEPARTEMENTS_REGION_DATA = load_departements_regions_data()
REGIONS_GEODATA = load_and_preprocess_regions_geographical_data()


def create_company_infos(company_data, receipts_agreements_data):
    company_component = CompanyComponent(company_data=company_data)

    receipts_agreements_component = ReceiptAgrementsComponent(receipts_agreements_data)

    full_layout = [
        dbc.Row(
            [
                dbc.Col(company_component.create_layout(), id="company-details", lg=3),
                dbc.Col(
                    receipts_agreements_component.create_layout(),
                    id="receipts-agrements-details",
                    lg=3,
                ),
                dbc.Col(
                    dcc.Markdown(
                        """
Les données pour cet établissement peuvent être consultées sur Trackdéchets.

Elles comprennent les bordereaux de suivi de déchets (BSD) dématérialisés, mais ne comprennent pas :
- les éventuels BSD papiers non dématérialisés,
- les bons d’enlèvements (huiles usagées et pneus)
- les annexes 1 (petites quantités)""",
                        id="general-infos",
                    ),
                    lg=3,
                ),
            ]
        )
    ]
    return full_layout


def create_bs_components_layouts(
    bs_data: pd.DataFrame,
    bs_revised_data: pd.DataFrame,
    siret: str,
    components_titles: List[str],
    components_ids: List[str],
) -> tuple:
    bs_created_revised_component = BSCreatedAndRevisedComponent(
        component_title=components_titles[0],
        company_siret=siret,
        bs_data=bs_data,
        bs_revised_data=bs_revised_data,
    )
    bs_created_revised_component_layout = bs_created_revised_component.create_layout()

    stock_component = StockComponent(
        component_title=components_titles[1],
        company_siret=siret,
        bs_data=bs_data,
    )
    stock_component_layout = stock_component.create_layout()

    annual_stats_component = BSStatsComponent(
        component_title=components_titles[2],
        company_siret=siret,
        bs_data=bs_data,
        bs_revised_data=bs_revised_data,
    )

    annual_stats_layout = annual_stats_component.create_layout()

    full_layout = [
        dbc.Row(
            [
                dbc.Col(
                    bs_created_revised_component_layout,
                    id=components_ids[0],
                    lg=3,
                    md=5,
                    sm=12,
                    class_name="col-framed",
                ),
                dbc.Col(
                    stock_component_layout,
                    id=components_ids[1],
                    lg=3,
                    md=5,
                    sm=12,
                    class_name="col-framed",
                ),
                dbc.Col(
                    annual_stats_layout,
                    id=components_ids[2],
                    lg=3,
                    md=5,
                    sm=12,
                    class_name="col-framed",
                ),
            ],
        )
    ]

    return full_layout


def create_bs_refusal_component(
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
        component_title=r"Bordereaux refusés en % de bordereaux émis",
        company_siret=siret,
        bs_data_dfs=dfs,
    )

    layout = bs_refusals_component.create_layout()

    if bs_refusals_component.is_component_empty:
        return no_update

    final_layout = dbc.Row(
        [
            dbc.Col(
                layout, id="bs-refusal", lg=3, md=5, sm=12, class_name="col-framed"
            ),
        ]
    )
    return final_layout


def create_onsite_waste_components(
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

    waste_origins_component = WasteOriginsComponent(
        component_title="Origine des déchets",
        company_siret=siret,
        bs_data_dfs=dfs,
        departements_regions_df=DEPARTEMENTS_REGION_DATA,
    )

    waste_origins_map_component = WasteOriginsMapComponent(
        component_title="Origine des déchets",
        company_siret=siret,
        bs_data_dfs=dfs,
        departements_regions_df=DEPARTEMENTS_REGION_DATA,
        regions_geodata=REGIONS_GEODATA,
    )

    final_layout = [
        dbc.Row(
            [
                dbc.Col(
                    storage_stats_component.create_layout(),
                    lg=3,
                    md=5,
                    sm=12,
                    id="waste-stock",
                    class_name="col-framed",
                ),
                dbc.Col(
                    waste_origins_component.create_layout(),
                    lg=3,
                    md=5,
                    sm=12,
                    id="waste-origins",
                    class_name="col-framed",
                ),
                dbc.Col(
                    waste_origins_map_component.create_layout(),
                    lg=3,
                    md=5,
                    sm=12,
                    id="waste-origins-map",
                    class_name="col-framed",
                ),
            ]
        ),
    ]

    return final_layout
