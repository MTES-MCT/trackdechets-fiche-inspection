select id,
    "createdAt",
    "siret",
    "name",
    "address"
from "default$default"."Company" c
where siret = '{siret}'