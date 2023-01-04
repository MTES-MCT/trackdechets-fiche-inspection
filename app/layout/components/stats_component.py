from datetime import datetime, timedelta, timezone
from typing import Dict
import re

import numpy as np
import pandas as pd
from dash_extensions.enrich import html

from .base_component import BaseComponent
from .utils import format_number_str


class BSStatsComponent(BaseComponent):
    """Component that displays aggregated data about 'bordereaux' and estimations of the onsite waste stock.

    Parameters
    ----------
    component_title : str
        Title of the component that will be displayed in the component layout.
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data: DataFrame
        DataFrame containing data for a given 'bordereau' type.
    bs_revised_data: DataFrame
        DataFrame containing list of revised 'bordereaux' for a given 'bordereau' type.
    """

    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bs_data: pd.DataFrame,
        bs_revised_data: pd.DataFrame = None,
    ) -> None:

        super().__init__(component_title, company_siret)

        self.bs_data = bs_data
        self.bs_revised_data = bs_revised_data

        self.emitted_bs_count = None
        self.archived_bs_count = None
        self.revised_bs_count = None
        self.more_than_one_month_bs_count = None
        self.total_incoming_weight = None
        self.total_outgoing_weight = None
        self.theorical_stock = None
        self.fraction_outgoing = None

    def _check_data_empty(self) -> bool:

        bs_data = self.bs_data
        siret = self.company_siret
        bs_data = bs_data[bs_data["emitterCompanySiret"] == siret]
        bs_revised_data = self.bs_revised_data

        if (len(bs_data) == 0) and (
            (bs_revised_data is None) or (len(bs_revised_data) == 0)
        ):
            self.is_component_empty = True
            return True

        self.is_component_empty = False
        return False

    def _preprocess_data(self) -> None:

        one_year_ago = (
            datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=365)
        ).strftime("%Y-%m-01")

        bs_data = self.bs_data
        bs_revised_data = self.bs_revised_data
        siret = self.company_siret

        self.emitted_bs_count = len(bs_data[bs_data["emitterCompanySiret"] == siret])
        self.archived_bs_count = len(
            bs_data[
                (bs_data["emitterCompanySiret"] == siret)
                & bs_data["status"].isin(["PROCESSED", "REFUSED", "NO_TRACEABILITY"])
            ]
        )
        self.revised_bs_count = (
            bs_revised_data["bsId"].nunique() if bs_revised_data is not None else 0
        )
        self.more_than_one_month_bs_count = len(
            bs_data[
                (bs_data["recipientCompanySiret"] == siret)
                & (
                    (bs_data["processedAt"] - bs_data["receivedAt"])
                    > np.timedelta64(1, "M")
                )
            ]
        )
        self.total_incoming_weight = bs_data.loc[
            (bs_data["recipientCompanySiret"] == siret)
            & (bs_data["receivedAt"] >= one_year_ago),
            "quantityReceived",
        ].sum()
        self.total_outgoing_weight = bs_data.loc[
            (bs_data["emitterCompanySiret"] == siret)
            & (bs_data["sentAt"] >= one_year_ago),
            "quantityReceived",
        ].sum()

        if self.total_outgoing_weight != 0:
            self.theorical_stock = (
                self.total_incoming_weight - self.total_outgoing_weight
            )
        else:
            self.theorical_stock = 0

        if self.total_incoming_weight != 0:
            self.fraction_outgoing = int(
                round(self.total_outgoing_weight / self.total_incoming_weight, 2) * 100
            )

    def _add_stats(self) -> None:

        self.component_layout.append(
            html.Div(
                [
                    html.P(
                        [
                            html.Span(
                                [format_number_str(self.emitted_bs_count, precision=0)],
                                className="sc-xl-number",
                            ),
                            "émis",
                        ]
                    )
                ],
                className="sc-primary",
            )
        )

        self.component_layout.append(
            html.Div(
                [
                    html.P(
                        [
                            html.Span(
                                [
                                    format_number_str(
                                        self.archived_bs_count, precision=0
                                    )
                                ],
                                className="sc-large-number",
                            ),
                            "archivés",
                        ]
                    ),
                    html.P(
                        [
                            html.Span(
                                [format_number_str(self.revised_bs_count, precision=0)],
                                className="sc-large-number",
                            ),
                            "corrigés",
                        ]
                    ),
                    html.P(
                        [
                            html.Span(
                                [
                                    format_number_str(
                                        self.more_than_one_month_bs_count, precision=0
                                    )
                                ],
                                className="sc-large-number",
                            ),
                            "réponses supérieures à un mois",
                        ]
                    ),
                ],
                className="sc-secondary",
            )
        )

        incoming_weight_bar_classname = "sc-complete-bar"
        if self.total_incoming_weight == 0:
            incoming_weight_bar_classname += "-error"

        if (self.total_outgoing_weight == 0) or (self.fraction_outgoing is None):
            style_outgoing_bar = {"gridColumn": "1 / 111"}
            style_stock_bar = {"display": "none"}
            outgoing_bar_classname = "sc-bar-consumed-error"
        elif self.fraction_outgoing > 100:
            style_outgoing_bar = {"gridColumn": "1 / 111"}
            style_stock_bar = {"display": "none"}
            outgoing_bar_classname = "sc-bar-consumed-error"
        else:
            style_outgoing_bar = {"gridColumn": f"1 / {max(self.fraction_outgoing,2)}"}
            style_stock_bar = {"gridColumn": f"{self.fraction_outgoing+2} / 102"}
            outgoing_bar_classname = "sc-bar-consumed"

        self.component_layout.append(
            html.Div(
                [
                    html.P(
                        [
                            html.Span(
                                [
                                    f"{format_number_str(self.total_incoming_weight, precision=1)}"
                                ],
                                className="sc-medium-number",
                            ),
                            "tonnes entrantes",
                        ],
                        className="sc-number-incoming",
                    ),
                    html.Div([], className=incoming_weight_bar_classname),
                    html.Div(
                        [],
                        className=outgoing_bar_classname,
                        style=style_outgoing_bar,
                    ),
                    html.Div(
                        [],
                        className="sc-bar-stock",
                        style=style_stock_bar,
                    ),
                    html.Div(
                        [
                            html.P(
                                [
                                    f"{format_number_str(self.total_outgoing_weight, precision=1)} tonnes sortantes"
                                ]
                            )
                        ],
                        className="sc-bar-number-outgoing",
                    ),
                    html.Div(
                        [
                            html.P(
                                [
                                    f"{format_number_str(self.theorical_stock, precision=1)} tonnes"
                                ]
                            ),
                            html.P(["stock théorique"]),
                        ],
                        className="sc-bar-number-stock",
                    ),
                ],
                className="sc-weight-bars",
            )
        )

    def create_layout(self) -> list:
        self._add_component_title()

        if self._check_data_empty():
            self._add_empty_block()
            return self.component_layout

        self._preprocess_data()
        self._add_stats()

        return self.component_layout


class StorageStatsComponent(BaseComponent):
    """Component that displays waste stock on site by waste codes (TOP 4) and total stock in tons.

    Parameters
    ----------
    component_title : str
        Title of the component that will be displayed in the component layout.
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the DataFrame containing the bordereau data.
    waste_codes_df: DataFrame
        DataFrame containing list of waste codes with their descriptions.
    """

    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bs_data_dfs: Dict[str, pd.DataFrame],
        waste_codes_df: pd.DataFrame,
    ) -> None:

        super().__init__(component_title, company_siret)

        self.bs_data_dfs = bs_data_dfs
        self.waste_codes_df = waste_codes_df

        self.stock_by_waste_code = None
        self.total_stock = None

    def _preprocess_data(self) -> pd.Series:

        siret = self.company_siret

        dfs_to_concat = [df for df in self.bs_data_dfs.values()]

        if len(dfs_to_concat) == 0:
            self.stock_by_waste_code = pd.Series()
            return

        df = pd.concat(dfs_to_concat)

        emitted_mask = (df.emitterCompanySiret == siret) & ~df.sentAt.isna()
        received_mask = (df.recipientCompanySiret == siret) & ~df.receivedAt.isna()
        emitted = df[emitted_mask].groupby("wasteCode")["quantityReceived"].sum()
        received = df[received_mask].groupby("wasteCode")["quantityReceived"].sum()

        stock_by_waste_code: pd.Series = (
            (-emitted + received).fillna(-emitted).fillna(received)
        )
        stock_by_waste_code.sort_values(ascending=False, inplace=True)

        stock_by_waste_code = stock_by_waste_code[stock_by_waste_code > 0]
        total_stock = format_number_str(stock_by_waste_code.sum(), precision=0)
        stock_by_waste_code = stock_by_waste_code.apply(format_number_str, precision=0)
        stock_by_waste_code = pd.merge(
            stock_by_waste_code,
            self.waste_codes_df,
            left_index=True,
            right_index=True,
            how="left",
            validate="one_to_one",
        )

        self.stock_by_waste_code = stock_by_waste_code
        self.total_stock = total_stock

    def _check_data_empty(self) -> bool:
        if (len(self.stock_by_waste_code) == 0) or self.stock_by_waste_code[
            "quantityReceived"
        ].isna().all():
            self.is_component_empty = True
            return True

        self.is_component_empty = False
        return False

    def _add_stats(self):

        tops_divs = []
        for row in self.stock_by_waste_code.head(4).itertuples():
            tops_divs.append(
                html.Div(
                    [
                        html.Div(
                            f"{row.quantityReceived}t",
                            className="sc-quantity-value",
                        ),
                        html.Div(
                            str(row.Index) + " - " + str(row.description),
                            className="sc-waste-code",
                        ),
                    ],
                    className="sc-stock-item",
                )
            )

        self.component_layout.append(
            html.Div(
                [
                    html.Div(
                        [html.Span(f"{self.total_stock}t"), "de déchets dangereux"],
                        id="sc-total-stock",
                    ),
                    html.Div(tops_divs, id="sc-top-waste-codes"),
                ],
                id="sc-content",
            )
        )

    def create_layout(self) -> list:
        self._add_component_title()
        self._preprocess_data()

        if self._check_data_empty():
            self._add_empty_block()
            return self.component_layout

        self._add_stats()

        return self.component_layout


class AdditionalInfoComponent(BaseComponent):
    """Component that displays additional informations like outliers quantities or inconsistent dates.

    Parameters
    ----------
    component_title : str
        Title of the component that will be displayed in the component layout.
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    additional_data: dict
        dict with additional data. The schema of the dict is like:
        {'date_outliers': {'BSDD': {'processedAt':some_DataFrame, 'sentAt': some_DataFrame}}, 'quantity_outliers': {'BSDD': some_DataFrame, 'BSDA': some_DataFrame, 'BSDASRI': some_DataFrame}}
    """

    def __init__(
        self,
        component_title: str,
        company_siret: str,
        additional_data: Dict[str, Dict[str, pd.DataFrame]],
    ) -> None:

        super().__init__(component_title, company_siret)

        self.additional_data = additional_data

        self.date_outliers_data = None
        self.quantity_outliers_data = None

    def _check_data_empty(self) -> bool:

        if (
            len(self.additional_data["date_outliers"])
            == len(self.additional_data["quantity_outliers"])
            == 0
        ):
            self.is_component_empty = True
            return self.is_component_empty

        self.is_component_empty = False
        return False

    def _preprocess_data(self) -> None:

        name_mapping = {
            "sentAt": "Date d'envoi",
            "receivedAt": "Date de réception",
            "processedAt": "Date de traitement",
        }

        date_outliers_data = {}
        for key, value in self.additional_data["date_outliers"].items():

            date_outliers_data[key] = {
                name_mapping[k]: v[k] for k, v in value.items() if v is not None
            }

        self.date_outliers_data = date_outliers_data
        self.quantity_outliers_data = self.additional_data["quantity_outliers"]

    def _add_date_outliers_layout(self) -> None:
        """Create and add the layout for date outliers."""

        data_outliers_bs_list_layout = []
        for bs_type, outlier_data in self.date_outliers_data.items():

            bs_col_example_li = []
            for col, serie in outlier_data.items():
                bs_col_example_li.append(
                    html.Li(
                        [
                            html.Span(f"{col} : ", className="fr-text--lg"),
                            f"{len(serie)} valeur(s) incohérente(s) (exemple de valeur : {serie.sample(1).item()})",
                        ],
                        className="fr-text--sm sc-date-outlier-example",
                    )
                )

            data_outliers_bs_list_layout.append(
                html.Li(
                    [
                        html.Div(
                            [
                                html.Div(
                                    f"{bs_type} :",
                                    className="fr-text--lg sc-outlier-date-bs-type",
                                ),
                                html.Button(
                                    "Télécharger les données correspondantes",
                                    id={
                                        "type": "download-outliers",
                                        "index": bs_type,
                                        "outlier_type": "date",
                                    },
                                    className="fr-text--xs sc-outlier-date-download-button",
                                ),
                            ],
                            className="sc-bs-outlier-list-header",
                        ),
                        html.Ul(bs_col_example_li),
                    ],
                    className="sc-bs-outliers-item",
                ),
            )

        date_outliers_layout = html.Div(
            [
                html.Div(
                    [
                        "Une ou plusieurs dates incohérentes ont été trouvées pour les types de bordereaux suivants :"
                    ]
                ),
                html.Ul(data_outliers_bs_list_layout, className="sc-bs-outliers-list"),
            ],
            id="sc-date-outliers",
        )

        self.component_layout.append(date_outliers_layout)

    def _add_quantity_outliers_layout(self) -> None:
        """Create and add the layout for quantity outliers."""

        quantity_outliers_bs_list_layout = []
        for bs_type, outlier_data in self.quantity_outliers_data.items():

            quantity_outliers_bs_list_layout.append(
                html.Li(
                    [
                        html.Div(
                            [
                                html.Span(f"{bs_type} : ", className="fr-text--lg"),
                                (
                                    f"{len(outlier_data)} quantité(s) incohérente(s) (exemple de valeur : "
                                    f"{format_number_str(outlier_data.quantityReceived.sort_values(ascending=False).head(1).item(),precision=0)}"
                                    " tonnes)"
                                ),
                            ]
                        ),
                        html.Button(
                            "Télécharger les données correspondantes",
                            id={
                                "type": "download-outliers",
                                "index": bs_type,
                                "outlier_type": "quantity",
                            },
                            className="fr-text--xs sc-outlier-quantity-download-button",
                        ),
                    ],
                    className="fr-text--sm  sc-outlier-quantity-example",
                )
            )

        quantity_outliers_layout = html.Div(
            [
                html.Div(
                    [
                        "Une ou plusieurs quantités incohérentes ont été trouvées pour les types de bordereaux suivants :"
                    ]
                ),
                html.Ul(
                    quantity_outliers_bs_list_layout, className="sc-bs-outliers-list"
                ),
            ],
            id="sc-quantity-outliers",
        )

        self.component_layout.append(quantity_outliers_layout)

    def create_layout(self) -> list:
        self._add_component_title()
        self._preprocess_data()

        if not self._check_data_empty():
            if len(self.date_outliers_data):
                self._add_date_outliers_layout()
            if len(self.quantity_outliers_data):
                self._add_quantity_outliers_layout()

        return self.component_layout


class ICPEItemsComponent(BaseComponent):
    """Component that displays list of ICPE authorized items.

    Parameters
    ----------
    component_title : str
        Title of the component that will be displayed in the component layout.
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    icpe_data: DataFrame
        DataFrame containing list of ICPE authorized items
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the DataFrame containing the bordereau data.

    """

    def __init__(
        self,
        component_title: str,
        company_siret: str,
        icpe_data: pd.DataFrame,
        bs_data_dfs: Dict[str, pd.DataFrame],
        mapping_processing_operation_code_rubrique: pd.DataFrame,
    ) -> None:

        super().__init__(component_title, company_siret)

        self.icpe_data = icpe_data
        self.bs_data_dfs = bs_data_dfs

        self.unit_pattern = re.compile(
            r"""^t$
                |^t\/.*$
                |citerne
                |bouteille
                |cabine
                |tonne
                |aire
                |cartouche
            """,
            re.X,
        )
        self.mapping_processing_operation_code_rubrique = (
            mapping_processing_operation_code_rubrique
        )

        self.on_site_2718_quantity = 0
        self.on_site_2760_quantity = 0
        self.avg_daily_2770_quantity = 0

    def _preprocess_data(self) -> None:

        preprocessed_inputs_dfs = []
        preprocessed_output_dfs = []
        actual_year = datetime.now().year
        for df in self.bs_data_dfs.values():
            df = df.dropna(subset=["processing_operation_code"])

            if len(df) == 0:
                continue

            df["processing_operation_code"] = df[
                "processing_operation_code"
            ].str.replace(" ", "", regex=False)

            df = pd.merge(
                df,
                self.mapping_processing_operation_code_rubrique,
                left_on="processing_operation_code",
                right_on="code_operation",
                validate="many_to_many",
                how="left",
            )

            preprocessed_inputs_dfs.append(
                df[
                    (df["recipientCompanySiret"] == self.company_siret)
                    & (df["processedAt"].dt.year == actual_year)
                ]
            )
            preprocessed_output_dfs.append(
                df[
                    (df["emitterCompanySiret"] == self.company_siret)
                    & (df["processedAt"].dt.year == actual_year)
                ]
            )

        if len(preprocessed_inputs_dfs) == 0:
            return

        preprocessed_inputs = pd.concat(preprocessed_inputs_dfs)
        quantity = preprocessed_inputs.loc[
            preprocessed_inputs["rubrique"] == "2718", "quantityReceived"
        ].sum()

        if len(preprocessed_output_dfs) > 0:
            preprocessed_outputs = pd.concat(preprocessed_output_dfs)
            quantity -= preprocessed_outputs.loc[
                preprocessed_outputs["rubrique"] == "2718", "quantityReceived"
            ].sum()

        if quantity > 0:
            self.on_site_2718_quantity = quantity

        quantity = preprocessed_inputs.loc[
            preprocessed_inputs["rubrique"] == "2760-1", "quantityReceived"
        ].sum()
        if quantity > 0:
            self.on_site_2760_quantity = quantity

        quantity = (
            preprocessed_inputs.loc[preprocessed_inputs["rubrique"] == "2770"]
            .groupby(pd.Grouper(key="processedAt", freq="1D"))["quantityReceived"]
            .sum()
            .mean()
        )
        if quantity > 0:
            self.avg_daily_2770_quantity = quantity

    def _add_items_list(self) -> None:

        icpe_data = pd.concat(
            [
                self.icpe_data.loc[
                    self.icpe_data["rubrique"].isin([2718, 2760, 2790, 2770])
                ],
                self.icpe_data.loc[
                    ~self.icpe_data["rubrique"].isin([2718, 2760, 2790])
                ].sort_values("rubrique"),
            ]
        )
        icpe_items_li_list = []
        for item in icpe_data.itertuples():

            rubrique_str = str(item.rubrique)
            if not pd.isna(item.alinea) and item.alinea != "None":
                rubrique_str += f"-{item.alinea}"

            on_site_quantity_div = html.Div()
            if (rubrique_str == "2718") and (self.on_site_2718_quantity > 0):
                quantity = format_number_str(self.on_site_2718_quantity, precision=0)
                on_site_quantity_div = html.Div(
                    [html.Span(f"{quantity} t"), " sur site"],
                    className="sc-onsite-quantity",
                )
            elif (rubrique_str == "2760-1") and (self.on_site_2760_quantity > 0):
                quantity = format_number_str(self.on_site_2760_quantity, precision=0)
                quantity_frac = int(100 * self.on_site_2760_quantity / item.volume)
                remaining_quantity = int(
                    100 - (100 * self.on_site_2760_quantity / item.volume)
                )
                style = {
                    "grid-column": f"1/{quantity_frac+2}",
                }
                style_remaining = {
                    "grid-column": f"{quantity_frac+2}/-1",
                }
                on_site_quantity_div = html.Div(
                    [
                        html.Div(
                            [],
                            style=style,
                            className="sc-grid-onsite-weight-bar",
                        ),
                        html.Div(
                            className="sc-grid-onsite-weight-remaining-bar",
                            style=style_remaining,
                        ),
                        html.Span(
                            f"{quantity} t reçues",
                            className="sc-grid-onsite-weight-value",
                        ),
                        html.Span(
                            f"{remaining_quantity} % restants",
                            className="sc-grid-onsite-weight-remaining-value",
                        ),
                    ],
                    className="sc-grid-onsite-quantity",
                )
            elif (rubrique_str == "2770") and (self.avg_daily_2770_quantity > 0):
                quantity = format_number_str(self.avg_daily_2770_quantity)
                on_site_quantity_div = html.Div(
                    [html.Span(f"{quantity} t/j"), " moyenne annuelle"],
                    className="sc-onsite-quantity",
                )

            authorization_str = "Pas de volume autorisé."
            volume = ""
            if not pd.isna(item.volume):
                volume = format_number_str(item.volume, precision=1)
                authorization_str = " unitée(s) autorisée(s)"

            unite = ""
            if not pd.isna(item.unite):
                unite = item.unite
                if re.match(self.unit_pattern, item.unite):
                    authorization_str = " autorisée(s)"
                else:
                    authorization_str = " autorisé(s)"

            dates = ""
            if not pd.isna(item.date_debut_exploitation) and not pd.isna(
                item.date_fin_validite
            ):
                dates += f" (valide du {item.date_debut_exploitation:%d-%m-%Y} au {item.date_fin_validite:%d-%m-%Y})"
            elif not pd.isna(item.date_debut_exploitation):
                dates += (
                    f" (valide à partir du {item.date_debut_exploitation:%d-%m-%Y})"
                )
            elif not pd.isna(item.date_fin_validite):
                dates += f" (valide jusqu'au {item.date_fin_validite:%d-%m-%Y})"

            icpe_items_li_list.append(
                html.Li(
                    [
                        html.Div(
                            f"{rubrique_str} - {item.libelle_court_activite.capitalize()} {dates}",
                            className="sc-icpe-item-title fr-text--lg",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(f"{volume} {unite}"),
                                        authorization_str,
                                    ],
                                    className="sc-item-quantity-authorized",
                                ),
                                on_site_quantity_div,
                            ],
                            className="sc-rubrique-item-details",
                        ),
                    ]
                )
            )

        self.component_layout.append(
            html.Ul(icpe_items_li_list, className="sc-icpe-item-list")
        )

    def _check_data_empty(self) -> bool:

        if len(self.icpe_data) == 0:
            self.is_component_empty = True
            return self.is_component_empty

        self.is_component_empty = False
        return False

    def create_layout(self) -> list:
        self._add_component_title()

        if not self._check_data_empty():
            self._preprocess_data()
            self._add_items_list()

        return self.component_layout


class TraceabilityInterruptionsComponent(BaseComponent):
    """Component that displays list of ICPE authorized items.

    Parameters
    ----------
    component_title : str
        Title of the component that will be displayed in the component layout.
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bsdd_data: DataFrame
        DataFrame containing bsdd data.


    """

    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bsdd_data: pd.DataFrame,
        waste_codes_df: pd.DataFrame,
    ) -> None:

        super().__init__(component_title, company_siret)

        self.preprocessed_data = None

        self.bsdd_data = bsdd_data
        self.waste_codes_df = waste_codes_df

    def _preprocess_data(self) -> None:

        if self.bsdd_data is None:
            return

        df_filtered = self.bsdd_data[
            self.bsdd_data["noTraceability"]
            & (self.bsdd_data["recipientCompanySiret"] == self.company_siret)
        ]

        if len(df_filtered) == 0:
            return

        df_grouped = df_filtered.groupby("wasteCode", as_index=False).agg(
            quantity=pd.NamedAgg(column="quantityReceived", aggfunc="sum"),
            count=pd.NamedAgg(column="id", aggfunc="count"),
        )

        final_df = pd.merge(
            df_grouped,
            self.waste_codes_df,
            left_on="wasteCode",
            right_index=True,
            how="left",
            validate="one_to_one",
        )

        final_df["quantity"] = final_df["quantity"].apply(
            format_number_str, precision=2
        )

        self.preprocessed_data = final_df

    def _check_data_empty(self) -> bool:

        if (self.preprocessed_data is None) or (len(self.preprocessed_data) == 0):
            self.is_component_empty = True
            return True

        return False

    def _add_stats(self) -> None:

        li_items = []

        for e in self.preprocessed_data.sort_values(
            "quantity", ascending=False
        ).itertuples():
            bordereau_str = "bordereaux"
            if e.quantity == 1:
                bordereau_str = bordereau_str[:-1]
            li_items.append(
                html.Li(
                    [
                        html.Div(
                            [
                                html.Div(
                                    f"{e.wasteCode}:", className="sc-tr-waste-code"
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"{e.count}", className="sc-tr-count"
                                        ),
                                        f" {bordereau_str}",
                                    ],
                                    className="sc-tr-num-bs",
                                ),
                                html.Div(
                                    [html.Span(f"{e.quantity}"), " tonnes"],
                                    className="sc-tr-quantity",
                                ),
                            ],
                            className="sc-tr-item-info",
                        ),
                        html.Div(e.description),
                    ],
                    className="sc-tr-list-item",
                )
            )

        self.component_layout.append(
            html.Div(
                [
                    html.Div(
                        "L'établissement a indique sur les BSD être autorisé à la rupture de traçabilité"
                        ", par arrêté préfectoral pour les déchets suivants:"
                    ),
                    html.Ul(li_items, id="sc-tr-list"),
                ]
            )
        )

    def create_layout(self) -> list:
        self._add_component_title()
        self._preprocess_data()

        if not self._check_data_empty():
            self._add_stats()
        else:
            self._add_empty_block()
        return self.component_layout
