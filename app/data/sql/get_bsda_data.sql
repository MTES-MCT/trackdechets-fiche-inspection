select
    id,
    "createdAt",
    "transporterTransportTakenOverAt" as "sentAt",
    "destinationReceptionDate" as "receivedAt",
    "destinationOperationDate" as "processedAt",
    "emitterCompanySiret",
    "emitterCompanyAddress",
    "destinationCompanySiret" as "recipientCompanySiret",
    "weightValue" as "wasteDetailsQuantity",
    "destinationReceptionWeight" as "quantityReceived",
    "wasteCode",
    "status"
from
    "default$default"."Bsda"
where
    ("emitterCompanySiret" = '{siret}'
        or "destinationCompanySiret" = '{siret}')
    and "isDeleted" = false
    and "createdAt" >= current_date - interval '1 year'
    and cast("status" as text) not in ('DRAFT', 'INITIAL', 'SIGNED_BY_WORKER')
order by
    "createdAt" asc