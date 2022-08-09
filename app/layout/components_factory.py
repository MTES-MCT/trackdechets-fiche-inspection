from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc

from .utils import format_number_str


def get_annual_stats_components(
    bs_data: pd.DataFrame, bs_revised_data: pd.DataFrame, siret: str
) -> list:

    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-01")

    emitted_bs_count = len(bs_data[bs_data["emitterCompanySiret"] == siret])
    archived_bs_count = len(
        bs_data[
            (bs_data["emitterCompanySiret"] == siret)
            & bs_data["status"].isin(["PROCESSED", "REFUSED", "NO_TRACEABILITY"])
        ]
    )
    revised_bs_count = len(bs_revised_data)
    more_than_one_month_bs_count = len(
        bs_data[
            (bs_data["recipientCompanySiret"] == siret)
            & (
                (bs_data["processedAt"] - bs_data["receivedAt"])
                > np.timedelta64(1, "M")
            )
        ]
    )
    total_incoming_weight = bs_data.loc[
        (bs_data["recipientCompanySiret"] == siret)
        & (bs_data["receivedAt"] >= one_year_ago),
        "quantityReceived",
    ].sum()
    total_outgoing_weight = bs_data.loc[
        (bs_data["emitterCompanySiret"] == siret) & (bs_data["sentAt"] >= one_year_ago),
        "wasteDetailsQuantity",
    ].sum()

    if total_outgoing_weight != 0:
        fraction_outgoing = int(
            round(total_outgoing_weight / total_incoming_weight, 2) * 100
        )
    else:
        fraction_outgoing = 0

    print(fraction_outgoing)
    theorical_stock = total_incoming_weight - total_outgoing_weight
    if fraction_outgoing > 100:
        style_end_column = {"gridColumn": "1 / 111"}
        style_stock_bar = {"display": False}
        outgoing_bar_classname = "bs-bar-consumed-error"
    else:
        style_end_column = {"gridColumn": f"1 / {fraction_outgoing}"}
        style_stock_bar = {"gridColumn": f"{fraction_outgoing+10} / 111"}
        outgoing_bar_classname = "bs-bar-consumed"

    component = [
        html.Div(["BSD dangereux sur l'année"], className="component-title"),
        html.Div(
            [
                html.P(
                    [
                        html.Span(
                            [format_number_str(emitted_bs_count)],
                            className="large-number-xl",
                        ),
                        "émis",
                    ]
                )
            ],
            className="stats-primary",
        ),
        html.Div(
            [
                html.P(
                    [
                        html.Span(
                            [format_number_str(archived_bs_count)],
                            className="large-number",
                        ),
                        "archivés",
                    ]
                ),
                html.P(
                    [
                        html.Span(
                            [format_number_str(revised_bs_count)],
                            className="large-number",
                        ),
                        "corrigés",
                    ]
                ),
                html.P(
                    [
                        html.Span(
                            [format_number_str(more_than_one_month_bs_count)],
                            className="large-number",
                        ),
                        "réponses supérieures à un mois",
                    ]
                ),
            ],
            className="stats-secondary",
        ),
        html.Div(
            [
                html.P(
                    [
                        html.Span(
                            [format_number_str(total_incoming_weight)],
                            className="medium-number",
                        ),
                        "tonnes entrantes",
                    ],
                    className="bs-stats-number-incoming",
                ),
                html.Div([], className="bs-complete-bar"),
                html.Div(
                    [],
                    className=outgoing_bar_classname,
                    style=style_end_column,
                ),
                html.Div(
                    [],
                    className="bs-bar-stock",
                    style=style_stock_bar,
                ),
                html.Div(
                    [
                        html.P(
                            [
                                f"{format_number_str(int(total_outgoing_weight))} tonnes sortantes"
                            ]
                        )
                    ],
                    className="bs-bar-number-outgoing",
                ),
                html.Div(
                    [
                        html.P([f"{format_number_str(int(theorical_stock))} tonnes"]),
                        html.P(["stock théorique"]),
                    ],
                    className="bs-bar-number-stock",
                ),
            ],
            className="bs-weight-bars",
        ),
    ]

    return component
