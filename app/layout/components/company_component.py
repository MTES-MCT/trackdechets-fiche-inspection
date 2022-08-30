from argparse import ArgumentError
from datetime import datetime, timedelta
from typing import Dict
from zoneinfo import ZoneInfo
from dash import html

from app.layout.components.base_component import BaseComponent


class CompanyComponent(BaseComponent):

    company_types_mapping = {
        "COLLECTOR": "Tri Transit Regroupement (TTR)",
        "WASTEPROCESSOR": "Usine de traitement",
        "WASTE_CENTER": "Déchetterie",
        "BROKER": "Courtier",
        "TRADER": "Négociant",
        "TRANSPORTER": "Transporteur",
        "ECO_ORGANISM": "Éco-organisme",
        "PRODUCER": "Producteur",
        "WASTE_VEHICLES": "Centre Véhicules Hors d'Usage",
    }

    def __init__(self, company_data: Dict[str, str]) -> None:
        self.company_data = company_data

        self.layout = None

    def create_layout(self) -> list:
        company_address = self.company_data["address"]
        company_siret = self.company_data["siret"]

        today_date = datetime.now(tz=ZoneInfo("Europe/Paris"))
        one_year_ago = today_date - timedelta(days=365)

        profiles_elements = []
        company_types = self.company_data["companyTypes"][1:-1].split(",")
        company_types_formatted = [
            self.company_types_mapping[ctype] for ctype in company_types
        ]

        for e in company_types_formatted:
            profiles_elements.append(html.Li(e))

        layout = [
            html.Div(f"SIRET : {company_siret}", id="cc-siret"),
            html.Div(
                [
                    html.Div("Profils établissements :", className="fr-text--bold"),
                    html.Ul(profiles_elements),
                ]
            ),
            html.Div(company_address, id="cc-address"),
            html.Div(
                [
                    html.Div(
                        f"Période du {one_year_ago:%d/%m/%Y} au {today_date:%d/%m/%Y}"
                    ),
                    html.Div(f"Fiche éditée le {today_date:%d/%m/%Y à %H:%M:%S}"),
                ]
            ),
        ]

        self.layout = layout

        return self.layout


class ReceiptAgrementsComponent(BaseComponent):
    def __init__(self, receipts_agreements_data: Dict[str, str]) -> None:

        self.receipts_agreements_data = receipts_agreements_data

        self.layout = None

    def _check_data_empty(self) -> bool:

        if len(self.receipts_agreements_data) == 0:
            return True

        return False

    def create_layout(self) -> list:

        if self._check_data_empty():
            return [
                html.Div(
                    "Pas de récépissés ou d'agréments enregistrés sur Trackdéchets pour cet établissement."
                )
            ]

        li_elements = []
        for name, data in self.receipts_agreements_data.items():
            for line in data.itertuples():
                validity_str = ""
                if "validityLimit" in line._fields:
                    if line.validityLimit < datetime.utcnow():
                        validity_str = f"expiré depuis le {line.validityLimit}"
                    else:
                        validity_str = f"valide jusqu'au {line.validityLimit:%d/%m/%Y}"

                li_elements.append(
                    html.Li(
                        [
                            html.Span(f"{name}", className="fr-text--bold"),
                            f" n°{line.receiptNumber} {validity_str}",
                        ]
                    )
                )

        layout = [
            html.Div("Agréments et récépissés déclarés sur Trackdéchets :"),
            html.Ul(li_elements),
        ]

        self.layout = layout

        return self.layout
