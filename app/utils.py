from os import getenv


def format_number_str(input_number) -> str:
    return "{:,.0f}".format(input_number).replace(",", " ")


def normalize_quantity_received(row) -> str:
    """Replace weights entered as kg instead of tons, and format the number in French fashion"""
    quantity = row["poids"]
    if quantity > (int(getenv("SEUIL_DIVISION_QUANTITE")) or 1000):
        quantity = quantity / 1000
    return quantity
