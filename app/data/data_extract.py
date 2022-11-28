import os
from pathlib import Path
from typing import Any, List

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = os.environ["DATABASE_URL"]
DWH_URL = os.environ["DWH_URL"]
DB_ENGINE = create_engine(DATABASE_URL)
DWH_ENGINE = create_engine(DWH_URL)
SQL_QUERIES_PATH = Path("app/data/sql")
STATIC_FILES_PATH = Path("app/data/static")


def make_query(
    sql_query_name: str,
    engine: str = "db-prod",
    date_columns: List[str] = None,
    dtypes: dict[str, Any] = None,
    **format_arguments,
) -> pd.DataFrame:
    """Make a SQL query using the sql file corresponding to the given sql query name.

    Parameters
    ----------
    sql_query_name : str
        Name of the sql file (without the .sql extension).
    date_columns : list of str
        Names of columns to parse as dates in pandas (time-zone aware dates are casted to UTC).
    dtypes: dict
        Dict mapping column name to corresponding dtype.
    format_arguments: kwargs
        Additional format arguments to pass to the SQL query.

    Returns
    -------
    DataFrame
        DataFrame with the result of the query.
    """

    if engine == "db-prod":
        con = DB_ENGINE
    elif engine == "dwh":
        con = DWH_ENGINE
    else:
        raise ValueError("engine must be either 'db-prod' or 'dwh'")

    sql_query_str = (
        (SQL_QUERIES_PATH / f"{sql_query_name}.sql")
        .read_text()
        .format(**format_arguments)
    )
    print(sql_query_str)

    date_params = None
    if date_columns is not None:
        date_params = {e: {"utc": True} for e in date_columns}
    df = pd.read_sql_query(
        sql_query_str, con=con, dtype=dtypes, parse_dates=date_params
    )

    return df


def load_departements_regions_data() -> pd.DataFrame:
    """Load geographical data (départements and regions) and returns it as a DataFrame.

    Columns included are :
    - code région
    - libellé region
    - code département
    - libellé département

    Returns
    -------
    DataFrame
        DataFrame with the regions and départements data.
    """

    df_departements = pd.read_csv(
        STATIC_FILES_PATH / "departement_2022.csv", dtype="str"
    )
    df_regions = pd.read_csv(STATIC_FILES_PATH / "region_2022.csv", dtype="str")
    dep_reg = pd.merge(
        df_departements,
        df_regions,
        left_on="REG",
        right_on="REG",
        how="left",
        validate="many_to_one",
        suffixes=("_dep", "_reg"),
    )

    return dep_reg


def load_waste_code_data() -> pd.DataFrame:
    """Load the nomenclature of waste and returns it as a DataFrame.

    Columns included are :
    - code
    - description

    Returns
    -------
    DataFrame
        DataFrame with the the nomenclature of waste.
    """

    df = pd.read_csv(
        STATIC_FILES_PATH / "code_dechets.csv", dtype="str", index_col="code"
    )
    assert df.index.is_unique

    return df


def load_and_preprocess_regions_geographical_data() -> gpd.GeoDataFrame:
    """Load the geojson of french regions, transform it to group overseas territories near metropolitan territory
    and returns it as a DataFrame.

    Columns included are :
    - code région
    - geometry

    Returns
    -------
    DataFrame
        GeoDataFrame with the the nomenclature of waste.
    """

    gdf = gpd.read_file(STATIC_FILES_PATH / "regions.geojson")

    translations = {
        "Guadeloupe": {"x": 55, "y": 30, "scale": 1.5},
        "Martinique": {"x": 56, "y": 31, "scale": 1.5},
        "La Réunion": {"x": -62, "y": 63, "scale": 1.5},
        "Mayotte": {"x": -50.5, "y": 54, "scale": 1.5},
        "Guyane": {"x": 47, "y": 40, "scale": 0.5},
    }
    for region, translation in translations.items():
        gdf.loc[gdf["nom"] == region, "geometry"] = (
            gdf.loc[gdf["nom"] == region, "geometry"]
            .translate(xoff=translation["x"], yoff=translation["y"], zoff=0.0)
            .scale(*(translation["scale"],) * 3)
        )

    return gdf
