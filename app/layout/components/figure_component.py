import logging
from datetime import datetime, timedelta
from typing import Dict, List, final
from functools import reduce

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from .base_component import BaseComponent

logger = logging.getLogger()


class FigureComponent(BaseComponent):
    def __init__(self, component_title: str, company_siret: str) -> None:
        super().__init__(component_title, company_siret)

        self.figure = None

        self.component_layout = []

    def _add_figure_block(self) -> None:

        self._create_figure()
        graph = dcc.Graph(
            figure=self.figure,
            config=dict(locale="fr"),
        )
        self.component_layout.append(graph)

    def _create_figure(self) -> None:
        raise NotImplementedError

    def create_layout(self) -> list:
        self._add_component_title()

        if self._check_data_empty():
            self._add_empty_block()
            return self.component_layout

        self._add_figure_block()

        return self.component_layout


class BSCreatedAndRevisedComponent(FigureComponent):
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

        if len(bs_emitted_by_month) == 0 and bs_revised_by_month is None:
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

        tick0_min = bs_emitted_by_month.index.min()
        max_y = bs_emitted_by_month.max()

        fig = go.Figure([bs_bars])
        if bs_revised_by_month is not None:
            fig.add_trace(
                go.Bar(
                    x=bs_revised_by_month.index,
                    y=bs_revised_by_month,
                    name="BSDD corrigés",
                    text=bs_revised_by_month,
                    textfont_size=text_size,
                    textposition="outside",
                    constraintext="none",
                )
            )
            tick0_min = min(
                bs_emitted_by_month.index.min(), bs_revised_by_month.index.min()
            )
            max_y = max(bs_emitted_by_month.max(), bs_revised_by_month.max())

        fig.update_layout(
            margin={"t": 20},
            legend={"orientation": "h", "y": -0.05, "x": 0.5},
        )

        fig.update_xaxes(
            dtick="M1",
            tickangle=0,
            tickformat="%b",
            tick0=tick0_min,
        )

        fig.update_yaxes(range=[0, max_y * 1.1])

        self.figure = fig

    def create_layout(self) -> list:

        self._preprocess_bs_data()
        if self.bs_revised_data is not None:
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
            legend={"orientation": "h", "y": -0.1, "x": 0.5},
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


class BSRefusalsComponent(FigureComponent):
    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bs_data_dfs: Dict[str, pd.DataFrame],
    ) -> None:

        super().__init__(component_title, company_siret)

        self.bs_data_dfs = bs_data_dfs

        self.preprocessed_series = None

    def _check_data_empty(self) -> bool:

        if self.preprocessed_series is None:
            return True

        for serie in self.preprocessed_series.values():

            if (serie is not None) and (len(serie) != 0) and (serie != 0).any():
                return False

        return True

    def _preprocess_data(self) -> None:
        def compute_perc_refusals(df: pd.DataFrame):
            df = df.copy()
            if len(df) == 0:
                return 0
            df_refused = df[df["status"] == "REFUSED"]
            res = len(df_refused) / len(df)
            return res

        preprocessed_series = {}
        for name, df in self.bs_data_dfs.items():
            preprocessed_serie = (
                df[df["emitterCompanySiret"] == self.company_siret]
                .groupby(pd.Grouper(key="createdAt", freq="1M"))
                .apply(compute_perc_refusals)
            )
            if len(preprocessed_serie) > 0:
                preprocessed_series[name] = preprocessed_serie

        self.preprocessed_series = preprocessed_series

    def _create_figure(self) -> None:

        traces = []

        mins = []
        for name, serie in self.preprocessed_series.items():

            trace = go.Scatter(x=serie.index, y=serie, name=name, mode="lines+markers")
            mins.append(serie.index.min())
            traces.append(trace)

        fig = go.Figure(traces)

        fig.update_layout(
            margin={"t": 20},
            legend={"orientation": "h", "y": -0.1, "x": 0.5},
            legend_font_size=11,
            showlegend=True,
        )
        fig.update_xaxes(
            tickangle=0,
            tickformat="%b",
            tick0=min(mins),
            dtick="M1",
        )

        self.figure = fig

    def create_layout(self) -> list:

        self._preprocess_data()
        super().create_layout()

        return self.component_layout


class WasteOrigineComponent(FigureComponent):
    def __init__(
        self,
        component_title: str,
        company_siret: str,
        bs_data_dfs: Dict[str, pd.DataFrame],
        departements_df: pd.DataFrame,
    ) -> None:
        super().__init__(component_title, company_siret)
        self.bs_data_dfs = bs_data_dfs
        self.departments_df = departements_df

        self.preprocessed_serie = None

    def _preprocess_bs_data(self) -> None:

        preprocessed_series = []
        for df in self.bs_data_dfs.values():

            df["cp"] = (
                df["emitterCompanyAddress"]
                .str.extract(r"([0-9]{5})", expand=False)
                .str[:2]
            )
            df = df.join(self.departments_df, on="cp")
            df["cp_formatted"] = df["LIBELLE"] + " (" + df["cp"] + ")"
            serie = (
                df[df["recipientCompanySiret"] == self.company_siret]
                .groupby("cp_formatted")["quantityReceived"]
                .sum()
            )
            preprocessed_series.append(serie)

        sum_serie: pd.Series = reduce(lambda x, y: x.add(y), preprocessed_series)

        for serie in preprocessed_series:
            sum_serie = sum_serie.fillna(serie)

        sum_serie.sort_values(ascending=False, inplace=True)

        final_serie = sum_serie[:5]
        final_serie["Autres origines"] = sum_serie[5:].sum()

        self.preprocessed_serie = final_serie

    def _check_data_empty(self) -> bool:

        if self.preprocessed_serie.isna().all() or len(self.preprocessed_serie) == 0:
            return True

        return False

    def _create_figure(self) -> None:

        # Prepare order for horizontal bar chart, preserving "Autre origines" has bottom bar
        serie = pd.concat(
            (self.preprocessed_serie[-1:], self.preprocessed_serie[-2::-1])
        )
        serie = serie.round(1)

        # The bar chart has invisible bar (at *_annot positions) that will hold the labels
        y_cats = [tup_e for e in serie.index for tup_e in (e, e + "_annot")]
        values = [tup_e for _, e in serie.items() for tup_e in (e, 0)]
        texts = [
            tup_e
            for index, value in serie.items()
            for tup_e in ("", f"<b>{value}t</b> - {index}")
        ]
        bar_trace = go.Bar(
            x=values,
            y=y_cats,
            orientation="h",
            text=texts,
            textfont_size=30,
            textposition="outside",
            width=[tup_e for e in values for tup_e in (0.7, 1)],
        )

        fig = go.Figure([bar_trace])
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, type="category")
        fig.update_layout(
            margin={"t": 20, "b": 0, "l": 0, "r": 0},
        )

        self.figure = fig

    def create_layout(self) -> list:

        self._preprocess_bs_data()
        super().create_layout()

        return self.component_layout
