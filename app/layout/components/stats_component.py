from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from app.layout.utils import format_number_str
from dash import html


class StatsComponent:
    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bs_data: pd.DataFrame,
        bs_revised_data: pd.DataFrame = None,
    ) -> None:

        self.component_title = component_title
        self.company_siret = company_siret
        self.bs_data = bs_data
        self.bs_revised_data = bs_revised_data

        self.component_layout = []

        self.emitted_bs_count = None
        self.archived_bs_count = None
        self.revised_bs_count = None
        self.more_than_one_month_bs_count = None
        self.total_incoming_weight = None
        self.total_outgoing_weight = None
        self.theorical_stock = None
        self.fraction_outgoing = None

    def _add_component_title(self) -> html.Div:
        self.component_layout.append(
            html.Div(
                self.component_title,
                className="sc-title",
            )
        )

    def _check_empty_data(self) -> bool:

        bs_data = self.bs_data
        siret = self.company_siret
        bs_data = bs_data[bs_data["emitterCompanySiret"] == siret]
        bs_revised_data = self.bs_revised_data

        if (len(bs_data) == 0) and (
            (bs_revised_data is None) or (len(bs_revised_data) == 0)
        ):
            return True
        return False

    def _add_empty_block(self) -> None:
        self.component_layout.append(
            html.Div(
                f"PAS DE DONNEES POUR LE SIRET {self.company_siret}",
                className="fc-empty-figure-block",
            )
        )

    def _create_stats(self) -> None:

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
            "wasteDetailsQuantity",
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
                                [format_number_str(self.emitted_bs_count)],
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
                                [format_number_str(self.archived_bs_count)],
                                className="sc-large-number",
                            ),
                            "archivés",
                        ]
                    ),
                    html.P(
                        [
                            html.Span(
                                [format_number_str(self.revised_bs_count)],
                                className="sc-large-number",
                            ),
                            "corrigés",
                        ]
                    ),
                    html.P(
                        [
                            html.Span(
                                [format_number_str(self.more_than_one_month_bs_count)],
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
            style_outgoing_bar = None
            style_stock_bar = None
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
                                [f"{self.total_incoming_weight:.1f}"],
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
                                [f"{self.total_outgoing_weight:.1f} tonnes sortantes"]
                            )
                        ],
                        className="sc-bar-number-outgoing",
                    ),
                    html.Div(
                        [
                            html.P([f"{self.theorical_stock:.1f} tonnes"]),
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

        if self._check_empty_data():
            self._add_empty_block()
            return self.component_layout

        self._create_stats()
        self._add_stats()

        return self.component_layout
