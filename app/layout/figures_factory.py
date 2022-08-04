import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def get_bsdd_created_and_revised_figure(
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
        title_text="BSD Dangeureux émis et corrigés",
        title_font_size=15,
        legend={"orientation": "h", "y": -0.15, "x": 0.5},
    )

    fig.update_xaxes(dtick="M1")

    max_value = max(bsdd_emitted.max(), bsdd_revised.max())
    fig.update_yaxes(range=[0, max_value * 1.1])

    return fig


def get_stock(bs_data: pd.DataFrame, siret: str) -> go.Figure:
    pass
