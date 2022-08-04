from pathlib import Path
from typing import List
from sqlalchemy import create_engine
import os
import pandas as pd

DATABASE_URL = os.environ["DATABASE_URL"]
SQL_ENGINE = create_engine(DATABASE_URL)
SQL_QUERIES_PATH = Path("app/data/sql")


def make_query(
    sql_query_name: str, date_columns: List[str] = None, **format_arguments
) -> pd.DataFrame:
    sql_query_str = (
        (SQL_QUERIES_PATH / f"{sql_query_name}.sql")
        .read_text()
        .format(**format_arguments)
    )
    print(sql_query_str)

    date_params = None
    if date_columns is not None:
        date_params = {e: {"utc": True} for e in date_columns}
    df = pd.read_sql(sql_query_str, con=SQL_ENGINE, parse_dates=date_params)

    return df
