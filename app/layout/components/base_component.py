from dash import html


class BaseComponent:
    """
    Base component class.
    A component consist of :
    - Data preprocessing methods;
    - HTML layout creation methods;
    - Method to check if the component is empty after data preprocessing (na data to display).

    Parameters
    ----------
    component_title : str
        Title of the component that will be displayed in the component layout.
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    is_component_empty: bool
        If True, the component has no data to display after preprocessing the data.
    component_layout: list of dash components
        Full layout of the component.
    """

    def __init__(self, component_title: str, company_siret: str = None) -> None:
        self.component_title = component_title
        self.company_siret = company_siret

        self.is_component_empty = None
        self.component_layout = []

    def _add_component_title(self) -> html.Div:
        """Add the component title to the layout.
        The title has the 'c-title' class by default.
        """

        self.component_layout.append(
            html.Div(
                self.component_title,
                className="c-title",
            )
        )

    def _add_empty_block(self) -> None:
        """Add a block to tell the component has no data to display.
        The empty block layout has the 'c-empty-figure-block' class by default.
        """
        self.component_layout.append(
            html.Div(
                f"PAS DE DONNEES POUR LE SIRET {self.company_siret}",
                className="c-empty-figure-block",
            )
        )

    def _check_data_empty(self) -> bool:
        """Logic to check if there is no data to display after preprocessing."""
        raise NotImplementedError()

    def _preprocess_data(self) -> None:
        """Data preprocessing logic."""
        raise NotImplementedError()

    def create_layout(self) -> list:
        """Create the component layout using the raw/preprocessed data.

        Returns
        -------
        list
            Layout as a list of dash components.
        """
        raise NotImplementedError()
