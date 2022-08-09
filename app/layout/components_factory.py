from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html
import dash_core_components as dcc

from .utils import format_number_str

INCOMING_STATUS = [
    "RECEIVED",
    "ACCEPTED",
    "PROCESSED",
    "GROUPED",
    "TEMP_STORED",
    "TEMP_STORER_ACCEPTED",
]
OUTGOING_STATUS = ["SENT", "RESENT", "PROCESSED"]


def get_bsdd_created_and_revised_component(
    bsdd_data: pd.DataFrame, bsdd_revised_data: pd.DataFrame, siret: str
) -> go.Figure:

    bsdd_emitted = (
        bsdd_data[bsdd_data["emitterCompanySiret"] == siret]
        .groupby(pd.Grouper(key="createdAt", freq="1M"))
        .id.count()
    )
    bsdd_revised = bsdd_revised_data.groupby(
        pd.Grouper(key="createdAt", freq="1M")
    ).id.count()

    textfont_size = 14
    bsdd_bars = go.Bar(
        x=bsdd_emitted.index,
        y=bsdd_emitted,
        name="BSDD émis",
        text=bsdd_emitted,
        textfont_size=textfont_size,
        textposition="outside",
        constraintext="none",
    )
    bsdd_revised_bar = go.Bar(
        x=bsdd_revised.index,
        y=bsdd_revised,
        name="BSDD corrigés",
        text=bsdd_revised,
        textfont_size=textfont_size,
    )

    fig = go.Figure([bsdd_bars, bsdd_revised_bar])

    fig.update_layout(
        margin={"t": 20},
        legend={"orientation": "h", "y": -0.05, "x": 0.5},
    )

    fig.update_xaxes(
        dtick="M1",
        tickangle=0,
        tickformat="%b",
        tick0=min(bsdd_emitted.index.min(), bsdd_revised.index.min()),
    )

    max_value = max(bsdd_emitted.max(), bsdd_revised.max())
    fig.update_yaxes(range=[0, max_value * 1.1])

    component = [
        html.Div(
            "BSD dangereux émis et corrigés",
            className="component-title",
        ),
        dcc.Graph(
            figure=fig,
            config=dict(locale="fr"),
        ),
    ]

    return component


def get_stock_component(bs_data: pd.DataFrame, siret: str) -> go.Figure:

    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-01")

    incoming_data = bs_data[
        (bs_data["recipientCompanySiret"] == siret)
        & (bs_data["sentAt"] >= one_year_ago)
        & bs_data["status"].isin(INCOMING_STATUS)
    ]
    outgoing_data = bs_data[
        (bs_data["emitterCompanySiret"] == siret)
        & (bs_data["receivedAt"] >= one_year_ago)
        & bs_data["status"].isin(OUTGOING_STATUS)
    ]

    incoming_data = incoming_data.groupby(pd.Grouper(key="sentAt", freq="1M"))[
        "quantityReceived"
    ].sum()
    outgoing_data = outgoing_data.groupby(pd.Grouper(key="receivedAt", freq="1M"))[
        "quantityReceived"
    ].sum()

    text_template = "%{x} - %{y:.0f} Tonnes"
    incoming_line = go.Scatter(
        x=incoming_data.index,
        y=incoming_data,
        name="Quantité entrante",
        mode="lines+markers",
        hovertemplate=text_template,
    )
    outgoing_line = go.Scatter(
        x=outgoing_data.index,
        y=outgoing_data,
        name="Quantité sortante",
        mode="lines+markers",
        hovertemplate=text_template,
    )

    fig = go.Figure(data=[incoming_line, outgoing_line])
    fig.update_layout(
        margin={"t": 20},
        legend={"orientation": "h", "y": -0.05, "x": 0.5},
        legend_font_size=11,
    )
    fig.update_xaxes(
        dtick="M1",
        tickangle=0,
        tickformat="%b",
        tick0=min(incoming_data.index.min(), outgoing_data.index.min()),
    )

    component = [
        html.Div(
            "Quantité de déchets dangereux en tonnes",
            className="component-title",
        ),
        dcc.Graph(
            figure=fig,
            config=dict(locale="fr"),
        ),
    ]

    return component


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
        & (bs_data["sentAt"] >= one_year_ago)
        & bs_data["status"].isin(INCOMING_STATUS),
        "quantityReceived",
    ].sum()
    total_outgoing_weight = bs_data.loc[
        (bs_data["emitterCompanySiret"] == siret)
        & (bs_data["receivedAt"] >= one_year_ago)
        & bs_data["status"].isin(OUTGOING_STATUS),
        "quantityReceived",
    ].sum()

    fraction_outgoing = int(
        round(total_outgoing_weight / total_incoming_weight, 2) * 100
    )
    print(fraction_outgoing)
    theorical_stock = total_incoming_weight - total_outgoing_weight
    if fraction_outgoing > 100:
        style_end_column = {"gridColumn": "1 / 111"}
        outgoing_bar_classname = "bs-bar-consumed-error"
    else:
        style_end_column = {"gridColumn": f"1 / {fraction_outgoing}"}
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
