select id,
    "createdAt",
    "siret",
    "name",
    "address",
    "companyTypes",
    "transporterReceiptId",
    "traderReceiptId",
    "ecoOrganismeAgreements",
    "brokerReceiptId",
    "vhuAgrementDemolisseurId",
    "vhuAgrementBroyeurId"
from "default$default"."Company" c
where c."siret" = '{siret}'