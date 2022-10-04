from typing import Dict, List, Tuple

import pandas as pd


def get_outliers_datetimes_df(
    df: pd.DataFrame, date_columns: List[str]
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """For a given DataFrame, separate lines with date outliers
    from lines with consistent (parsable) dates in provided list of date columns.

    Parameters
    ----------
    df : DataFrame
        DataFrame with raw (str) date data.
    date_columns : list of str
        Names of columns to parse as dates in pandas (time-zone aware dates are casted to UTC).

    Returns
    -------
    Tuple consisting of :
    1. DataFrame with consistent dates.
    2. Dict with keys being date column names and values being the DataFrame's lines with inconsistent date for this column.
    """
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
    """Filter out lines from 'bordereau' DataFrame with inconsistent received quantity.
    The rules to identify outliers in received quantity are business rules and may be tweaked in the future.

    Parameters
    ----------
    df : DataFrame
        DataFrame with 'bordereau' data.
    bs_type : str
        Name of the 'bordereau' (BSDD, BSDA, BSFF, BSVHU or BSDASRI).

    Returns
    -------
    DataFrame
        DataFrame with lines with received quantity outliers removed.
    """

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
