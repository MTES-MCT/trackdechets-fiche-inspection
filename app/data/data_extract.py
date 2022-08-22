import os
from pathlib import Path
from typing import List

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = os.environ["DATABASE_URL"]
SQL_ENGINE = create_engine(DATABASE_URL)
SQL_QUERIES_PATH = Path("app/data/sql")
STATIC_FILES_PATH = Path("app/data/static")


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


def load_departements_regions_data() -> pd.DataFrame:

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

    df = pd.read_csv(
        STATIC_FILES_PATH / "code_dechets.csv", dtype="str", index_col="code"
    )
    assert df.index.is_unique()

    return df


def load_and_preprocess_regions_geographical_data() -> gpd.GeoDataFrame:

    gdf = gpd.read_file(
        "/Users/luis/projects/entropeak/trackdechets/trackdechets-fiche-inspection/app/data/static/regions.geojson"
    )

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
