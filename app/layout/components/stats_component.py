from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd
from dash import html

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

        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-01")

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
            len(bs_revised_data) if bs_revised_data is not None else 0
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
                                        "type": "download-date-outliers",
                                        "index": bs_type,
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
                        html.Span(f"{bs_type} : ", className="fr-text--lg"),
                        f"{len(outlier_data)} quantité(s) incohérente(s) (exemple de valeur : {format_number_str(outlier_data.quantityReceived.sort_values(ascending=False).head(1).item(),precision=0)} tonnes)",
                    ],
                    className="fr-text--sm sc-date-outlier-example",
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
    ) -> None:

        super().__init__(component_title, company_siret)

        self.icpe_data = icpe_data

        self.bs_data_dfs = bs_data_dfs

    def _add_items_list(self) -> None:

        icpe_items_li_list = []
        for item in self.icpe_data.itertuples():
            rubrique_str = str(item.rubrique)
            if item.alinea is not None:
                rubrique_str += f" {item.alinea}"

            authorization_str = "Pas de volume autorisé."
            volume = ""
            if not pd.isna(item.volume):
                volume = format_number_str(item.volume, precision=1)
                authorization_str = " autorisés"

            unite = ""
            if item.unite is not None:
                unite = item.unite

            icpe_items_li_list.append(
                html.Li(
                    [
                        html.Div(
                            f"{rubrique_str} - {item.libelle_court_activite.capitalize()}",
                            className="sc-icpe-item-title fr-text--lg",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(f"{volume}{unite}"),
                                        authorization_str,
                                    ],
                                    className="sc-item-quantity-authorized",
                                )
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
            self._add_items_list()

        return self.component_layout
