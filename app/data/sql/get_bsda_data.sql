select
    id,
    "createdAt",
    "transporterTransportTakenOverAt" as "sentAt",
    "destinationReceptionDate" as "receivedAt",
    "destinationOperationDate" as "processedAt",
    "emitterCompanySiret",
    "destinationCompanySiret" as "recipientCompanySiret",
    "weightValue" as "wasteDetailsQuantity",
    "destinationReceptionWeight" as "quantityReceived",
    "status"
 from
    "default$default"."Bsda"
where
    ("emitterCompanySiret" = '{siret}'
    or "destinationCompanySiret" = '{siret}')
    and "isDeleted" = false
    and "createdAt" >= current_date - INTERVAL '1 year'
    order by "createdAt" asc