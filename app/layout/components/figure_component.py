from datetime import datetime, timedelta
from dash import html, dcc
import pandas as pd
import plotly.graph_objects as go
import logging

logger = logging.getLogger()


class FigureComponent:
    def __init__(self, component_title: str, company_siret: str) -> None:
        self.component_title = component_title
        self.company_siret = company_siret

        self.figure = None

        self.component_layout = []

    def _add_component_title(self) -> html.Div:
        self.component_layout.append(
            html.Div(
                self.component_title,
                className="fc-title",
            )
        )

    def _add_empty_figure_block(self) -> None:
        self.component_layout.append(
            html.Div(
                f"PAS DE DONNES POUR LE SIRET {self.company_siret}",
                className="fc-empty-figure-block",
            )
        )

    def _add_figure_block(self) -> None:

        self._create_figure()
        graph = dcc.Graph(
            figure=self.figure,
            config=dict(locale="fr"),
        )
        self.component_layout.append(graph)

    def _create_figure(self) -> None:
        raise NotImplementedError

    def _check_data_empty(self) -> bool:
        raise NotImplementedError

    def create_layout(self) -> list:
        self._add_component_title()

        if self._check_data_empty():
            self._add_empty_figure_block()
            return self.component_layout

        self._add_figure_block()

        return self.component_layout


class BSCreatedAndRevisedComponent(FigureComponent):
    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bs_data: pd.DataFrame,
        bs_revised_data: pd.DataFrame,
    ) -> None:

        super().__init__(component_title, company_siret)
        self.bs_data = bs_data
        self.bs_revised_data = bs_revised_data
        self.bs_emitted_by_month = None
        self.bs_revised_by_month = None

    def _preprocess_bs_data(self) -> None:

        bs_data = self.bs_data

        bs_emitted_by_month = (
            bs_data[bs_data["emitterCompanySiret"] == self.company_siret]
            .groupby(pd.Grouper(key="createdAt", freq="1M"))
            .id.count()
        )

        self.bs_emitted_by_month = bs_emitted_by_month

    def _preprocess_bs_revised_data(self) -> None:

        bs_revised_data = self.bs_revised_data

        bs_revised_by_month = bs_revised_data.groupby(
            pd.Grouper(key="createdAt", freq="1M")
        ).id.count()

        self.bs_revised_by_month = bs_revised_by_month

    def _check_data_empty(self) -> bool:

        bs_emitted_by_month = self.bs_emitted_by_month
        bs_revised_by_month = self.bs_revised_by_month

        if len(bs_emitted_by_month) == len(bs_revised_by_month) == 0:
            return True

        if bs_emitted_by_month.isna().all() and bs_revised_by_month.isna().all():
            return True

        return False

    def _create_figure(self) -> None:

        bs_emitted_by_month = self.bs_emitted_by_month
        bs_revised_by_month = self.bs_revised_by_month

        text_size = 14

        bs_bars = go.Bar(
            x=bs_emitted_by_month.index,
            y=bs_emitted_by_month,
            name="BSDD émis",
            text=bs_emitted_by_month,
            textfont_size=text_size,
            textposition="outside",
            constraintext="none",
        )
        bs_revised_bar = go.Bar(
            x=bs_revised_by_month.index,
            y=bs_revised_by_month,
            name="BSDD corrigés",
            text=bs_revised_by_month,
            textfont_size=text_size,
            textposition="outside",
            constraintext="none",
        )

        fig = go.Figure([bs_bars, bs_revised_bar])

        fig.update_layout(
            margin={"t": 20},
            legend={"orientation": "h", "y": -0.05, "x": 0.5},
        )

        fig.update_xaxes(
            dtick="M1",
            tickangle=0,
            tickformat="%b",
            tick0=min(bs_emitted_by_month.index.min(), bs_revised_by_month.index.min()),
        )

        max_value = max(bs_emitted_by_month.max(), bs_revised_by_month.max())
        fig.update_yaxes(range=[0, max_value * 1.1])

        self.figure = fig

    def create_layout(self) -> list:

        self._preprocess_bs_data()
        self._preprocess_bs_revised_data()

        super().create_layout()

        return self.component_layout


class StockComponent(FigureComponent):
    def __init__(self, component_title: str, company_siret: str, bs_data) -> None:
        super().__init__(component_title, company_siret)

        self.bs_data = bs_data

        self.incoming_data_by_month = None
        self.outgoing_data_by_month = None

    def _preprocess_data(self) -> None:

        bs_data = self.bs_data
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-01")

        incoming_data = bs_data[
            (bs_data["recipientCompanySiret"] == self.company_siret)
            & (bs_data["receivedAt"] >= one_year_ago)
        ]
        outgoing_data = bs_data[
            (bs_data["emitterCompanySiret"] == self.company_siret)
            & (bs_data["sentAt"] >= one_year_ago)
        ]

        self.incoming_data_by_month = incoming_data.groupby(
            pd.Grouper(key="receivedAt", freq="1M")
        )["quantityReceived"].sum()

        self.outgoing_data_by_month = outgoing_data.groupby(
            pd.Grouper(key="sentAt", freq="1M")
        )["wasteDetailsQuantity"].sum()

    def _check_data_empty(self) -> bool:

        incoming_data_by_month = self.incoming_data_by_month
        outgoing_data_by_month = self.outgoing_data_by_month

        if len(incoming_data_by_month) == len(outgoing_data_by_month) == 0:
            return True

        if incoming_data_by_month.isna().all() and outgoing_data_by_month.isna().all():
            return True

        return False

    def _create_figure(self) -> None:

        incoming_data_by_month = self.incoming_data_by_month
        outgoing_data_by_month = self.outgoing_data_by_month

        text_template = "%{x} - %{y:.0f} Tonnes"

        incoming_line = go.Scatter(
            x=incoming_data_by_month.index,
            y=incoming_data_by_month,
            name="Quantité entrante",
            mode="lines+markers",
            hovertemplate=text_template,
        )
        outgoing_line = go.Scatter(
            x=outgoing_data_by_month.index,
            y=outgoing_data_by_month,
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
            tickangle=0,
            tickformat="%b",
            tick0=min(
                incoming_data_by_month.index.min(), outgoing_data_by_month.index.min()
            ),
            dtick="M1",
        )

        self.figure = fig

    def create_layout(self) -> list:

        self._preprocess_data()
        super().create_layout()

        return self.component_layout
