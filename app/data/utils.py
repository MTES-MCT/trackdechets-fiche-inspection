from typing import Dict, List, Tuple
import pandas as pd


def get_outliers_datetimes_df(
    df: pd.DataFrame, date_columns: List[str]
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    df = df.copy()
    outliers = {}
    idx_with_outliers = set()

    for colname in date_columns:
        time_data = pd.to_datetime(df[colname], errors="coerce")
        outliers_df = df[time_data.isna() & (~df[colname].isin(["None", "NaT"]))]
        if len(outliers_df) > 0:
            idx_with_outliers.update(outliers_df.index.tolist())
            outliers[colname] = outliers_df.to_json()

    if len(idx_with_outliers) > 0:
        df = df[~df.index.isin(idx_with_outliers)]

    for colname in date_columns:
        df[colname] = pd.to_datetime(df[colname].replace("None", pd.NaT))

    return df, outliers


def get_quantity_outliers(df: pd.DataFrame, bs_type: str) -> pd.DataFrame:

    df = df.copy()
    if bs_type in ["BSDD", "BSDA"]:
        df_quantity_outliers = df[
            (df["quantityReceived"] > 40) & (df["transporterTransportMode"] == "ROAD")
        ]
    elif bs_type == "BSDASRI":
        df_quantity_outliers = df[
            (df["quantityReceived"] > 20) & (df["transporterTransportMode"] == "ROAD")
        ]
    elif bs_type == "BSVHU":
        df_quantity_outliers = df[(df["quantityReceived"] > 40)]
    elif bs_type == "BSFF":
        df_quantity_outliers = df[df["quantityReceived"] > 20]

    return df_quantity_outliers
