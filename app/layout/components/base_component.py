from dash import html


class BaseComponent:
    def __init__(self, component_title: str, company_siret: str) -> None:
        self.component_title = component_title
        self.company_siret = company_siret

        self.is_component_empty = None
        self.component_layout = []

    def _add_component_title(self) -> html.Div:
        self.component_layout.append(
            html.Div(
                self.component_title,
                className="c-title",
            )
        )

    def _add_empty_block(self) -> None:
        self.component_layout.append(
            html.Div(
                f"PAS DE DONNEES POUR LE SIRET {self.company_siret}",
                className="c-empty-figure-block",
            )
        )

    def _check_data_empty(self) -> bool:
        raise NotImplementedError
