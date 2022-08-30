import re
from typing import List
import pandas as pd
import numpy as np


def get_code_departement(code_postal: str):
    if pd.isna(code_postal):
        return np.nan
    if 20000 <= int(code_postal) < 21000:
        if int(code_postal) <= 20190:
            return "2A"
        else:
            return "2B"
    if int(code_postal) > 97000:
        return code_postal[:3]

    return code_postal[:2]


def format_number_str(input_number: float, precision: int = 2) -> str:
    input_number = round(input_number, precision)
    return re.sub(r"\.0+", "", "{:,}".format(input_number).replace(",", " "))
