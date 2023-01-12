"""
Dash dash_app configuration
"""
import locale
from os import getenv

import dash_auth
import diskcache
from dash import DiskcacheManager
from dash_extensions.enrich import DashProxy, ServersideOutputTransform

from app.layout.layout_factory import get_layout

locale.setlocale(locale.LC_ALL, "fr_FR")

auth_data = {"trackdechets": getenv("APP_PASSWORD")}
external_scripts = ["https://cdn.plot.ly/plotly-locale-fr-latest.js"]

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)


dash_app = DashProxy(
    __name__,
    title="Fiche d'inspection",
    external_scripts=external_scripts,
    long_callback_manager=background_callback_manager,
    transforms=[ServersideOutputTransform()],
)

auth = dash_auth.BasicAuth(dash_app, auth_data)

dash_app.layout = get_layout()


# Add the @lang attribute to the root <html>
dash_app.index_string = dash_app.index_string.replace("<html>", '<html lang="fr">')
# print(dash_app.index_string)
