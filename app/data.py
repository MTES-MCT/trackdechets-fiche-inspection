"""
Data gathering and processing
"""
import pandas as pd
import sqlalchemy
from datetime import datetime as dt
import locale
import re

from app.cache_config import cache_timeout, appcache
from app.time_config import *
import app.utils

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

# Lpg export recyclage
# SIRET = '90008481500019'


def get_company_data() -> pd.DataFrame:
    """
    Queries the configured database for company data.
    :return: dataframe of companies for a given period of time, with their creation week
    """
    df_company_query = pd.read_sql_query(
        'SELECT "Company"."siret", "Company"."name", "Company"."address",' '"Company"."contactPhone",'
        '"Company"."contactEmail", "Company"."website", installation."codeS3ic" '
        'FROM "default$default"."Company" '
        'LEFT JOIN'
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
        'SELECT "id", date_trunc(\'month\', "sentAt") as mois, "emitterCompanyAddress", "emitterWorkSitePostalCode",'
        '"quantityReceived" as poids, \'émis\' as origine, "wasteAcceptationStatus" as acceptation '
        'FROM "default$default"."Form" '
        f'WHERE "emitterCompanySiret" = \'{SIRET}\' '
        'AND "default$default"."Form"."sentAt" >= date_trunc(\'month\','
        f"CAST((CAST(now() AS timestamp) + (INTERVAL '-{str(time_delta_m)} month')) AS timestamp)) "
        'AND "default$default"."Form"."isDeleted" = FALSE '
        'UNION ALL '
        'SELECT "id", date_trunc(\'month\', "receivedAt") as mois, "emitterCompanyAddress", '
        '"emitterWorkSitePostalCode", '
        '"quantityReceived" as poids, \'reçus\' as origine, '
        '"wasteAcceptationStatus" as acceptation '
        'FROM "default$default"."Form" '
        f'WHERE "recipientCompanySiret" = \'{SIRET}\' '
        'AND "default$default"."Form"."receivedAt" >= date_trunc(\'month\','
        f"CAST((CAST(now() AS timestamp) + (INTERVAL '-{str(time_delta_m)} month')) AS timestamp)) "
        'AND "default$default"."Form"."isDeleted" = FALSE ',
        con=engine,
    )
    return df_bsdd_query


df_bsdd = get_bsdd_data()
emis = df_bsdd.query('origine == "émis"')
emis_nb = emis.index.size
recus = df_bsdd.query('origine == "reçus"')
recus_nb = recus.index.size


#
# BSDD / acceptation / mois
#

acceptation = {
    'ACCEPTED': 'Accepté',
    'REFUSED': 'Refusé',
    'PARTIALLY_REFUSED': 'Part. refusé'
}

df_bsdd_acceptation_mois: pd.DataFrame = emis[['id', 'mois', 'acceptation']].copy()
df_bsdd_acceptation_mois = df_bsdd_acceptation_mois.groupby(by=['mois', 'acceptation'], as_index=False, dropna=False).\
    count()
df_bsdd_acceptation_mois['mois'] = [dt.strftime(date, "%b/%y")
                                    for date in df_bsdd_acceptation_mois['mois']]
df_bsdd_acceptation_mois['acceptation'] = [acceptation[val] if isinstance(val, str) else "n/a"
                                           for val in df_bsdd_acceptation_mois['acceptation']]
#
# BSDD / origine / poids / mois
#

df_bsdd["poids"] = df_bsdd.apply(
    app.utils.normalize_quantity_received, axis=1
)

bsdd_grouped_poids_mois = get_bsdd_data()[['poids', 'origine', 'mois']].groupby(by=['mois', 'origine'],
                                                                                as_index=False).sum()
bsdd_grouped_poids_mois['mois'] = [dt.strftime(date, "%b/%y") for date in bsdd_grouped_poids_mois['mois']]
bsdd_grouped_poids_mois['poids'] = bsdd_grouped_poids_mois['poids'].apply(round)

#
# BSDD / reçus / département
#


def set_departement(row):
    worksite_address = row.emitterWorkSitePostalCode
    company_address = row.emitterCompanyAddress

    result = re.findall(r'(\d{2})\d{3}', worksite_address)

    if len(result) == 2:
        return result
    else:
        return re.findall(r'(\d{2})\d{3}', company_address)


df_bsdd_origine_poids: pd.DataFrame = recus[['emitterCompanyAddress', 'poids']].copy()
df_bsdd_origine_poids['departement_origine'] = df_bsdd_origine_poids['emitterCompanyAddress'].str.\
                                                   extract(r"(\d{2})\d{3}")
df_bsdd_origine_poids = df_bsdd_origine_poids[['departement_origine', 'poids']].\
    groupby(by='departement_origine', as_index=False).sum()
df_bsdd_origine_poids['poids'] = df_bsdd_origine_poids['poids'].apply(round)
df_bsdd_origine_poids.sort_values(by='poids', ascending=True, inplace=True)
df_bsdd_origine_poids = df_bsdd_origine_poids.tail(10)
departements = pd.read_csv('app/assets/departement.csv', index_col='DEP')
df_bsdd_origine_poids = df_bsdd_origine_poids.merge(departements, left_on='departement_origine', right_index=True)
df_bsdd_origine_poids['LIBELLE'] = df_bsdd_origine_poids['LIBELLE'] + ' (' \
                                   + df_bsdd_origine_poids['poids'].astype(str) + ' t)'

print()
