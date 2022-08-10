from app.layout.components.figure_component import (
    BSCreatedAndRevisedComponent,
    StockComponent,
)
from app.layout.components.stats_component import StatsComponent
import pandas as pd


def create_bs_components_layouts(
    bs_data: pd.DataFrame, bs_revised_data: pd.DataFrame, siret: str
) -> tuple:
    bs_created_revised_component = BSCreatedAndRevisedComponent(
        component_title="BSD Dangereux émis et corrigés",
        company_siret=siret,
        bs_data=bs_data,
        bs_revised_data=bs_revised_data,
    )
    bs_created_revised_component_layout = bs_created_revised_component.create_layout()

    stock_component = StockComponent(
        component_title="Quantité de déchets dangereux en tonnes",
        company_siret=siret,
        bs_data=bs_data,
    )
    stock_component_layout = stock_component.create_layout()

    annual_stats_component = StatsComponent(
        component_title="BSD dangereux sur l'année",
        company_siret=siret,
        bs_data=bs_data,
        bs_revised_data=bs_revised_data,
    )

    annual_stats_layout = annual_stats_component.create_layout()

    return (
        bs_created_revised_component_layout,
        stock_component_layout,
        annual_stats_layout,
    )
