"""
Data gathering and processing
"""
import pandas as pd
import sqlalchemy

from app.cache_config import cache_timeout, appcache
from app.time_config import *

# postgresql://admin:admin@localhost:5432/ibnse
engine = sqlalchemy.create_engine(getenv("DATABASE_URL"))


@appcache.memoize(timeout=cache_timeout)
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
        f'WHERE "siret" = \'{getenv("SIRET")}\'',

        con=engine,
    )
    return df_company_query

