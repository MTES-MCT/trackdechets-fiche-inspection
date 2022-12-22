select
   id,
    "createdAt",
    "transporterTakenOverAt" as "sentAt",
    "destinationReceptionDate" as "receivedAt",
    "destinationOperationSignatureDate" as "processedAt",
    "emitterCompanySiret",
    "emitterCompanyAddress",
    "destinationCompanySiret" as "recipientCompanySiret",
    "emitterWasteWeightValue" as "wasteDetailsQuantity",
    "destinationReceptionWasteWeightValue"/1000 as "quantityReceived",
    "wasteCode",
    "destinationOperationCode" as "processing_operation_code",
    "status",
    "transporterTransportMode"
from
    "default$default"."Bsdasri" 
where
    ("emitterCompanySiret" = '{siret}'
        or "destinationCompanySiret" = '{siret}')
    and "isDeleted" = false
    and "createdAt" >= current_date - interval '1 year'
    and cast("status" as text) not in ('DRAFT', 'INITIAL', 'SIGNED_BY_WORKER')
order by
    "createdAt" asc