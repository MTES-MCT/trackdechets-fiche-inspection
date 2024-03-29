import logging
from typing import Dict, List

import pandas as pd
from dash_extensions.enrich import dcc, html

from app.data.data_extract import (
    load_and_preprocess_regions_geographical_data,
    load_departements_regions_data,
    load_mapping_rubrique_processing_operation_code,
    load_waste_code_data,
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
    AdditionalInfoComponent,
    BSStatsComponent,
    ICPEInfoComponent,
    ICPEItemsComponent,
    StorageStatsComponent,
    TraceabilityInterruptionsComponent,
)
from app.layout.components.table_component import InputOutputWasteTableComponent

logger = logging.getLogger()

DEPARTEMENTS_REGION_DATA = load_departements_regions_data()
REGIONS_GEODATA = load_and_preprocess_regions_geographical_data()
WASTE_CODES_DATA = load_waste_code_data()
PROCESSING_OPERATION_CODE_RUBRIQUE_MAPPING = (
    load_mapping_rubrique_processing_operation_code()
)


def create_company_infos(
    company_data: pd.Series, receipts_agreements_data: Dict[str, pd.DataFrame]
) -> list:
    """Creates the components about company (general information and receipts/agreements info) and returns layout.

    Parameters
    ----------
    company_data : pandas Series
        Series with company general information.
    receipts_agreements_data : dict
        Dict with keys being the name of the receipt/agreement and values being DataFrames
        with one line per receipt/agreement (usually there is only one receipt for a receipt type for an establishment but
        there might be more).

    Returns
    -------
    list of dash components
        Layout to insert into main layout.
    """

    company_component = CompanyComponent(company_data=company_data)

    receipts_agreements_component = ReceiptAgrementsComponent(receipts_agreements_data)

    full_layout = [
        html.Div(
            company_component.create_layout(),
            id="company-details",
            className="col-print",
        ),
        html.Div(
            receipts_agreements_component.create_layout(),
            id="receipts-agrements-details",
            className="col-print",
        ),
        html.Div(
            dcc.Markdown(
                """
Les données pour cet établissement peuvent être consultées sur Trackdéchets.

Elles comprennent les bordereaux de suivi de déchets (BSD) dématérialisés, mais ne comprennent pas :
- les éventuels BSD papiers non dématérialisés,
- les bons d’enlèvements (huiles usagées et pneus)
- les annexes 1 (petites quantités)""",
                id="general-infos",
            ),
            className="col-print",
        ),
    ]

    return full_layout


def create_bs_components_layouts(
    bs_data: pd.DataFrame,
    company_data: pd.Series,
    components_titles: List[str],
    components_ids: List[str],
) -> list:
    """Creates the components about a type of 'bordereau' and returns layout with the three related component.

    Parameters
    ----------
    bs_data: DataFrame
        DataFrame containing data for a given 'bordereau' type.
    company_data : Series
        Series containing company data.
    components_titles : list of str
        Titles of the three different components in the order they appears in the layout.
    components_ids : list of str
        ids of the of the three different components in the order they appears in the layout.

    Returns
    -------
    list of dash components
        Layout to insert into main layout.

    """

    siret = company_data["siret"]

    bs_data_df = bs_data["bs_data"]

    if bs_data.get("bs_revised_data") is not None:
        bs_revised_data_df = bs_data["bs_revised_data"]
    else:
        bs_revised_data_df = None

    bs_created_revised_component = BSCreatedAndRevisedComponent(
        component_title=components_titles[0],
        company_siret=siret,
        bs_data=bs_data_df,
        bs_revised_data=bs_revised_data_df,
    )
    bs_created_revised_component_layout = bs_created_revised_component.create_layout()

    stock_component = StockComponent(
        component_title=components_titles[1],
        company_siret=siret,
        bs_data=bs_data_df,
    )
    stock_component_layout = stock_component.create_layout()

    annual_stats_component = BSStatsComponent(
        component_title=components_titles[2],
        company_siret=siret,
        bs_data=bs_data_df,
        bs_revised_data=bs_revised_data_df,
    )

    annual_stats_layout = annual_stats_component.create_layout()

    are_all_components_empty = all(
        e.is_component_empty
        for e in [bs_created_revised_component, stock_component, annual_stats_component]
    )

    if are_all_components_empty:
        return [html.Div()]

    full_layout = [
        html.Div(
            bs_created_revised_component_layout,
            id=components_ids[0],
            className="col-framed col-print",
        ),
        html.Div(
            stock_component_layout,
            id=components_ids[1],
            className="col-framed col-print",
        ),
        html.Div(
            annual_stats_layout,
            id=components_ids[2],
            className="col-framed col-print",
        ),
    ]

    return full_layout


def create_complementary_figure_components(
    company_data: pd.Series,
    bsdd_data: Dict[str, pd.DataFrame],
    bsda_data: Dict[str, pd.DataFrame],
    bsff_data: Dict[str, pd.DataFrame],
    bsdasri_data: Dict[str, pd.DataFrame],
    bsvhu_data: Dict[str, pd.DataFrame],
    additional_data: Dict[str, Dict[str, pd.DataFrame]],
) -> html.Div:
    """Creates the components about refused 'bordereaux' and complementary informations about outliers
    and returns layout.

    Parameters
    ----------
    company_data : dict
        Serialized company data.
    bsdd_data: dict
        dict with DataFrame containing data for BSDDs.
    bsda_data: dict
        dict with DataFrame containing data for BSDAs.
    bsff_data: dict
        dict with DataFrame containing data for BSFFs.
    bsdasri_data: dict
        dict with DataFrame containing data for BSDASRIs.
    bsvhu_data: dict
        dict with DataFrame containing data for BSVHUs.
    additional_data : dict
        Dict of DataFrame containing outliers data. Key are 'bordereau' type and values are outliers.

    Returns
    -------
    list of dash components
        Layout to insert into main layout.
    """

    final_layout = []

    siret = company_data["siret"]

    dfs = {
        "Déchets Dangereux": bsdd_data,
        "Amiante": bsda_data,
        "Fluides Frigo": bsff_data,
        "DASRI": bsdasri_data,
        "VHU": bsvhu_data,
    }
    dfs = {k: v.get("bs_data") for k, v in dfs.items() if v is not None}

    bs_refusals_component = BSRefusalsComponent(
        component_title=r"Nombre de bordereaux refusés",
        company_siret=siret,
        bs_data_dfs=dfs,
    )

    bs_refusals_component.create_layout()

    if not bs_refusals_component.is_component_empty:
        final_layout.append(
            html.Div(
                bs_refusals_component.component_layout,
                id="bs-refusal",
                className="col-framed  col-print",
            )
        )

    if (
        len(additional_data["date_outliers"]) > 0
        or len(additional_data["quantity_outliers"]) > 0
    ):

        for outlier_type, outlier_dict in additional_data.items():

            for bs_type, d in outlier_dict.items():

                if outlier_type == "date_outliers":
                    for colname, value in d.items():
                        additional_data["date_outliers"][bs_type][colname] = (
                            value if value is not None else None
                        )
                if outlier_type == "quantity_outliers":
                    additional_data["quantity_outliers"][bs_type] = (
                        d if d is not None else None
                    )

        additional_info_component = AdditionalInfoComponent(
            "Informations complémentaires",
            company_siret=siret,
            additional_data=additional_data,
        )

        final_layout.append(
            html.Div(
                additional_info_component.create_layout(),
                id="bs-additional-info",
                className="col-framed  col-print",
            )
        )

    return final_layout


def create_onsite_waste_components(
    company_data: pd.Series,
    bsdd_data: pd.DataFrame,
    bsda_data: pd.DataFrame,
    bsff_data: pd.DataFrame,
    bsdasri_data: pd.DataFrame,
    bsvhu_data: pd.DataFrame,
) -> list:
    """Creates the components about on site wastes (three components).

    Parameters
    ----------
    company_data : Series
        Series containing company data.
    bsdd_data: str
        DataFrame containing data for BSDDs.
    bsda_data: str
        DataFrame containing data for BSDAs.
    bsff_data: str
        DataFrame containing data for BSFFs.
    bsdasri_data: str
        DataFrame containing data for BSDASRIs.
    bsvhu_data: str
        DataFrame containing data for BSVHUs.

    Returns
    -------
    list of dash components
        Layout to insert into main layout.
    """

    siret = company_data["siret"]

    dfs = {
        "Déchets Dangereux": bsdd_data,
        "Amiante": bsda_data,
        "Fluides Frigo": bsff_data,
        "DASRI": bsdasri_data,
        "VHU": bsvhu_data,
    }
    dfs = {k: v.get("bs_data") for k, v in dfs.items() if v is not None}

    storage_stats_component = StorageStatsComponent(
        component_title="Déchets entreposés sur site actuellement",
        company_siret=siret,
        bs_data_dfs=dfs,
        waste_codes_df=WASTE_CODES_DATA,
    )

    storage_stats_component_layout = storage_stats_component.create_layout()

    waste_origins_component = WasteOriginsComponent(
        component_title="Origine des déchets",
        company_siret=siret,
        bs_data_dfs=dfs,
        departements_regions_df=DEPARTEMENTS_REGION_DATA,
    )
    waste_origins_component_layout = waste_origins_component.create_layout()

    waste_origins_map_component = WasteOriginsMapComponent(
        component_title="Origine des déchets",
        company_siret=siret,
        bs_data_dfs=dfs,
        departements_regions_df=DEPARTEMENTS_REGION_DATA,
        regions_geodata=REGIONS_GEODATA,
    )

    waste_origins_map_component_layout = waste_origins_map_component.create_layout()

    are_all_components_empty = all(
        e.is_component_empty
        for e in [
            storage_stats_component,
            waste_origins_component,
            waste_origins_map_component,
        ]
    )

    if are_all_components_empty:
        return [html.Div()], {"display": "block"}

    final_layout = [
        html.Div(
            storage_stats_component_layout,
            id="waste-stock",
            className="col-framed col-print",
        ),
        html.Div(
            waste_origins_component_layout,
            id="waste-origins",
            className="col-framed col-print",
        ),
        html.Div(
            waste_origins_map_component_layout,
            id="waste-origins-map",
            className="col-framed col-print",
        ),
    ]

    return final_layout, {"display": "none"}


def create_waste_input_output_table_component(
    company_data: pd.Series,
    bsdd_data: pd.DataFrame,
    bsda_data: pd.DataFrame,
    bsff_data: pd.DataFrame,
    bsdasri_data: pd.DataFrame,
    bsvhu_data: pd.DataFrame,
) -> list:
    """Creates the table component with the list of inbound and outbound wastes.

    Parameters
    ----------
    company_data : Series
        Series containing company data.
    bsdd_data: DataFrame
        DataFrame containing data for BSDDs.
    bsda_data: DataFrame
        DataFrame containing data for BSDAs.
    bsff_data: DataFrame
        DataFrame containing data for BSFFs.
    bsdasri_data: DataFrame
        DataFrame containing data for BSDASRIs.
    bsvhu_data: DataFrame
        DataFrame containing data for BSVHUs.


    Returns
    -------
    list of dash components
        Layout to insert into main layout.

    """

    siret = company_data["siret"]

    dfs = {
        "Déchets Dangereux": bsdd_data,
        "Amiante": bsda_data,
        "Fluides Frigo": bsff_data,
        "DASRI": bsdasri_data,
        "VHU": bsvhu_data,
    }

    dfs = {k: v.get("bs_data") for k, v in dfs.items() if v is not None}

    input_output_waste_component = InputOutputWasteTableComponent(
        "Déchets entrants sortants par code déchet",
        company_siret=siret,
        bs_data_dfs=dfs,
        waste_codes_df=WASTE_CODES_DATA,
    )
    layout = input_output_waste_component.create_layout()

    if not input_output_waste_component.is_component_empty:
        return [
            html.Div(
                layout,
            )
        ], {"display": "none"}
    else:
        return [html.Div()], {"display": "block"}


def create_icpe_components(
    company_data: pd.Series,
    icpe_data: pd.DataFrame,
    bsdd_data: pd.DataFrame,
    bsda_data: pd.DataFrame,
    bsff_data: pd.DataFrame,
    bsdasri_data: pd.DataFrame,
    bsvhu_data: pd.DataFrame,
) -> tuple:

    siret = company_data["siret"]

    if all(
        e is None
        for e in [icpe_data, bsdd_data, bsda_data, bsff_data, bsdasri_data, bsvhu_data]
    ):
        return [html.Div()], {"display": "block"}

    final_layout = []
    if any(
        e is not None
        for e in [icpe_data, bsdd_data, bsda_data, bsff_data, bsdasri_data, bsvhu_data]
    ):

        dfs = {
            "Déchets Dangereux": bsdd_data,
            "Amiante": bsda_data,
            "Fluides Frigo": bsff_data,
            "DASRI": bsdasri_data,
            "VHU": bsvhu_data,
        }
        dfs = {k: v.get("bs_data") for k, v in dfs.items() if v is not None}

        icpe_info_component = ICPEInfoComponent(
            component_title="Informations sur l'établissement",
            company_siret=siret,
            icpe_data=icpe_data,
            bs_data_dfs=dfs,
            mapping_processing_operation_code_rubrique=PROCESSING_OPERATION_CODE_RUBRIQUE_MAPPING,
        )

        icpe_info_component_layout = icpe_info_component.create_layout()

        if not icpe_info_component.is_component_empty:
            final_layout.append(
                html.Div(
                    icpe_info_component_layout,
                    className="col-framed col-print",
                    id="icpe-info-component",
                )
            )

    if icpe_data is not None:

        icpe_items_component = ICPEItemsComponent(
            "Rubriques ICPE autorisées",
            company_siret=siret,
            icpe_data=icpe_data,
            bs_data_dfs=dfs,
            mapping_processing_operation_code_rubrique=PROCESSING_OPERATION_CODE_RUBRIQUE_MAPPING,
        )

        icpe_items_layout = icpe_items_component.create_layout()

        if not icpe_items_component.is_component_empty:
            final_layout.append(
                html.Div(
                    icpe_items_layout,
                    className="col-framed col-print",
                    id="icpe-items-component",
                ),
            )

    traceability_interruption_component = TraceabilityInterruptionsComponent(
        component_title="Rupture de traçabilité",
        company_siret=siret,
        bsdd_data=dfs["Déchets Dangereux"],
        waste_codes_df=WASTE_CODES_DATA,
    )

    traceability_interruption_component_layout = (
        traceability_interruption_component.create_layout()
    )

    if not traceability_interruption_component.is_component_empty:
        final_layout.append(
            html.Div(
                traceability_interruption_component_layout,
                className="col-framed col-print",
                id="traceability-interruption-component",
            )
        )

    if len(final_layout):
        return final_layout, {"display": "none"}
    else:
        return [html.Div()], {"display": "block"}
