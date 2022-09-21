from typing import Dict
import pandas as pd
from .base_component import BaseComponent
from dash import dcc, dash_table, html


class InputOutputWasteTableComponent(BaseComponent):
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

        self.preprocessed_df = None

    def _preprocess_data(self) -> None:
        siret = self.company_siret

        dfs_to_concat = [df for df in self.bs_data_dfs.values()]

        if len(dfs_to_concat) == 0:
            self.preprocessed_df = pd.DataFrame()
            return

        df = pd.concat(dfs_to_concat)
        df = df[(df.emitterCompanySiret == siret) | (df.recipientCompanySiret == siret)]
        df["entrant/sortant"] = df.apply(
            lambda x: "sortant" if x["emitterCompanySiret"] == siret else "entrant",
            axis=1,
        )

        df_grouped = df.groupby(["wasteCode", "entrant/sortant"], as_index=False)[
            "quantityReceived"
        ].sum()

        final_df = pd.merge(
            df_grouped,
            self.waste_codes_df,
            left_on="wasteCode",
            right_index=True,
            how="left",
            validate="many_to_one",
        )

        final_df = final_df[final_df["quantityReceived"] > 0]

        self.preprocessed_df = (
            final_df[
                ["wasteCode", "description", "entrant/sortant", "quantityReceived"]
            ]
            .sort_values(by=["wasteCode", "entrant/sortant"])
            .rename(
                columns={"wasteCode": "Code déchet", "quantityReceived": "Quantité (t)"}
            )
        )

    def _check_empty_data(self) -> bool:
        if len(self.preprocessed_df) == 0:
            self.is_component_empty = True
            return True

        self.is_component_empty = False
        return False

    def _add_layout(self) -> None:

        self.component_layout.append(
            dash_table.DataTable(
                data=self.preprocessed_df.to_dict("records"),
                columns=[{"id": c, "name": c} for c in self.preprocessed_df.columns],
                page_size=1000000,
                style_cell={
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "maxWidth": 0,
                },
            )
        )

    def create_layout(self) -> list():
        self._add_component_title()
        self._preprocess_data()

        if self._check_empty_data():
            self._add_empty_block()
            return self.component_layout

        self._add_layout()

        return self.component_layout
