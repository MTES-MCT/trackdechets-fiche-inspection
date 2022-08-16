from datetime import datetime, timedelta
from typing import Dict
from zoneinfo import ZoneInfo
from dash import html


class CompanyComponent:
    def __init__(self, company_data: Dict[str, str]) -> None:
        self.company_data = company_data

        self.layout = None

    def create_layout(self) -> list:
        company_address = self.company_data["address"]
        company_siret = self.company_data["siret"]

        today_date = datetime.now(tz=ZoneInfo("Europe/Paris"))
        one_year_ago = today_date - timedelta(days=365)

        layout = [
            html.Div(f"SIRET : {company_siret}", id="cc-siret"),
            html.Div(company_address, id="cc-address"),
            html.Div(
                [
                    html.Div(
                        f"Période du {one_year_ago:%d %B %Y} au {today_date:%d %B %Y}"
                    ),
                    html.Div(f"Fiche éditée le {today_date:%d %B %Y à %H:%M:%S}"),
                ]
            ),
        ]

        self.layout = layout

        return self.layout
