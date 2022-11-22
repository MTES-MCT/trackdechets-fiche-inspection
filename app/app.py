"""
Dash dash_app configuration
"""
import locale
from os import getenv

import dash
import dash_auth
import dash_bootstrap_components as dbc
import diskcache


from app.layout.layout_factory import get_layout

locale.setlocale(locale.LC_ALL, "fr_FR")

auth_data = {"trackdechets": getenv("APP_PASSWORD")}
external_scripts = ["https://cdn.plot.ly/plotly-locale-fr-latest.js"]

cache = diskcache.Cache("./cache")
background_callback_manager = dash.DiskcacheManager(cache)

# Use [dbc.themes.BOOTSTRAP] to import the full Bootstrap CSS
dash_app = dash.Dash(
    __name__,
    title="Fiche d'inspection",
    external_stylesheets=[dbc.themes.GRID],
    external_scripts=external_scripts,
    long_callback_manager=background_callback_manager,
)

auth = dash_auth.BasicAuth(dash_app, auth_data)

dash_app.layout = get_layout()


# Add the @lang attribute to the root <html>
dash_app.index_string = dash_app.index_string.replace("<html>", '<html lang="fr">')
# print(dash_app.index_string)
