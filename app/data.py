"""
Data gathering and processing
"""
import pandas as pd
import sqlalchemy
from datetime import datetime as dt
import locale
from app.cache_config import cache_timeout, appcache
from app.time_config import *

# postgresql://admin:admin@localhost:5432/ibnse
engine = sqlalchemy.create_engine(getenv("DATABASE_URL"))

locale.setlocale(locale.LC_ALL, 'fr_FR')

# Arc en ciel
# SIRET = '33303497300029'
# MARTIN
# SIRET = '31176579600017'
# SECHE ALLIANCE (pas dans ICPE)
# SIRET = '55685027900051'
# SARP
SIRET = '30377298200029'


def get_company_data() -> pd.DataFrame:
    """
    Queries the configured database for company data.
    :return: dataframe of companies for a given period of time, with their creation week
    """
    df_company_query = pd.read_sql_query(
        'SELECT "Company"."siret", "Company"."name", "Company"."address",' '"Company"."contactPhone",'
        '"Company"."contactEmail", "Company"."website", installation."codeS3ic" '
        'FROM "default$default"."Company" '
        'INNER JOIN'
        '"default$default"."Installation" as installation '
        'on "siret" = installation."s3icNumeroSiret" '
        f'WHERE "siret" = \'{SIRET}\'',

        con=engine,
    )
    return df_company_query


def get_bsdd_data() -> pd.DataFrame:
    """
    Queries the configured database for the BSDD data for a given company.
    :return: dataframe of bsdds for a given period of time and a given company
    """
    df_bsdd_query = pd.read_sql_query(
        'SELECT "id", date_trunc(\'month\', "sentAt") as mois,'
        '"quantityReceived" as poids, \'émis\' as origine '
        'FROM "default$default"."Form" '
        f'WHERE "emitterCompanySiret" = \'{SIRET}\' '
        'AND "default$default"."Form"."sentAt" >= date_trunc(\'month\','
        f"CAST((CAST(now() AS timestamp) + (INTERVAL '-{str(time_delta_m)} month')) AS timestamp)) "
        'UNION ALL '
        'SELECT "id", date_trunc(\'month\', "receivedAt") as mois,'
        '"quantityReceived" as poids, \'recus\' as origine '
        'FROM "default$default"."Form" '
        f'WHERE "recipientCompanySiret" = \'{SIRET}\' '
        'AND "default$default"."Form"."receivedAt" >= date_trunc(\'month\','
        f"CAST((CAST(now() AS timestamp) + (INTERVAL '-{str(time_delta_m)} month')) AS timestamp))",
        con=engine,
    )
    return df_bsdd_query


def normalize_quantity_received(row) -> float:
    """Replace weights entered as kg instead of tons"""
    quantity = row["poids"]
    if quantity > (int(getenv("SEUIL_DIVISION_QUANTITE")) or 1000):
        quantity = quantity / 1000
    return quantity


df_bsdd = get_bsdd_data()
df_bsdd["poids"] = df_bsdd.apply(
    normalize_quantity_received, axis=1
)

bsdd_grouped_nb_mois = get_bsdd_data()[['id', 'origine', 'mois']].groupby(by=['origine', 'mois'],
                                                                          as_index=False).count()
bsdd_grouped_nb_mois['mois'] = [dt.strftime(date, "%b/%y") for date in bsdd_grouped_nb_mois['mois']]

