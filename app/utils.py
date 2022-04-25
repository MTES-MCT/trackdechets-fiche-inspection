from os import getenv
import re


def format_number_str(input_number) -> str:
    return "{:,.0f}".format(input_number).replace(",", " ")


def normalize_quantity_received(row) -> str:
    """Replace weights entered as kg instead of tons, and format the number in French fashion"""
    quantity = row["poids"]
    if quantity > (int(getenv("SEUIL_DIVISION_QUANTITE")) or 1000):
        quantity = quantity / 1000
    return quantity


def set_departement(row):
    worksite_address = row.emitterWorkSitePostalCode
    company_address = row.emitterCompanyAddress

    result = re.findall(r'(\d{2})\d{3}', worksite_address)

    if len(result) == 2:
        return result
    else:
        return re.findall(r'(\d{2})\d{3}', company_address)
