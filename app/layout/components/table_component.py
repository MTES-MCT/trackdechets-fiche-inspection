from typing import Dict

import pandas as pd
from dash_extensions.enrich import dash_table

from .base_component import BaseComponent
from .utils import format_number_str


class InputOutputWasteTableComponent(BaseComponent):
    """Component that displays an exhaustive tables with input and output wastes classified by waste codes.

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

        self.preprocessed_df = None

    def _preprocess_data(self) -> None:
        siret = self.company_siret

        dfs_to_concat = [df for df in self.bs_data_dfs.values()]

        if len(dfs_to_concat) == 0:
            self.preprocessed_df = pd.DataFrame()
            return

        df = pd.concat(dfs_to_concat)
        df = df[(df.emitterCompanySiret == siret) | (df.recipientCompanySiret == siret)]
        df["Entrant/Sortant"] = df.apply(
            lambda x: "sortant➡️" if x["emitterCompanySiret"] == siret else "➡️entrant",
            axis=1,
        )

        df_grouped = (
            df.groupby(["wasteCode", "Entrant/Sortant"], as_index=False)[
                "quantityReceived"
            ]
            .sum()
            .round(2)
        )

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
                ["wasteCode", "description", "Entrant/Sortant", "quantityReceived"]
            ]
            .sort_values(by=["wasteCode", "Entrant/Sortant"])
            .rename(
                columns={
                    "wasteCode": "Code déchet",
                    "quantityReceived": "Quantité (t)",
                    "description": "Description",
                }
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
                columns=[
                    {"id": c, "name": c, "selectable": False}
                    if c != "Quantité (t)"
                    else {
                        "id": c,
                        "name": c,
                        "selectable": False,
                        "format": dash_table.Format.Format(
                            group=True, groups=[3], group_delimiter=" "
                        ),
                        "type": "numeric",
                    }
                    for c in self.preprocessed_df.columns
                ],
                cell_selectable=False,
                page_size=1000000,
                style_cell={
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "maxWidth": 0,
                },
                style_data_conditional=[
                    {
                        "if": {
                            "column_id": "Entrant/Sortant",
                            "filter_query": "{Entrant/Sortant} = '➡️ entrant'",
                        },
                        "font-weight": 700,
                    },
                    {
                        "if": {
                            "column_id": "Entrant/Sortant",
                            "filter_query": "{Entrant/Sortant} = 'sortant ➡️'",
                        },
                        "font-weight": 700,
                    },
                    {
                        "if": {"column_id": "Code déchet"},
                        "width": "125px",
                        "maxWidth": "1155px",
                        "text-align": "left",
                    },
                    {
                        "if": {"column_id": "Entrant/Sortant"},
                        "width": "175px",
                        "maxWidth": "175px",
                        "text-align": "center",
                    },
                    {
                        "if": {"column_id": "Quantité (t)"},
                        "width": "145px",
                        "maxWidth": "145px",
                        "font-weight": "bold",
                    },
                    {"if": {"column_id": "Description"}, "text-align": "left"},
                ],
                style_header={"text-align": "center"},
                sort_action="native",
                sort_mode="single",
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
