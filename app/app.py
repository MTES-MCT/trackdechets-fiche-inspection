"""
Dash dash_app configuration
"""
import dash_bootstrap_components as dbc
from os import getenv
import dash_auth
import dash

external_scripts = ["https://cdn.plot.ly/plotly-locale-fr-latest.js"]
extra_config = {"locale": "fr"}

auth_data = {
    'trackdechets': getenv('APP_PASSWORD')
}

# Use [dbc.themes.BOOTSTRAP] to import the full Bootstrap CSS
dash_app = dash.Dash(
    __name__,
    title="Fiche d'inspection",
    external_stylesheets=[dbc.themes.GRID],
    external_scripts=external_scripts,
)

auth = dash_auth.BasicAuth(
    dash_app,
    auth_data
)

# Add the @lang attribute to the root <html>
dash_app.index_string = dash_app.index_string.replace('<html>', '<html lang="fr">')
# print(dash_app.index_string)
