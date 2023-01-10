select
    id,
    "createdAt",
    "sentAt",
    "receivedAt",
    "processedAt",
    "emitterCompanySiret",
    "emitterCompanyAddress",
    "recipientCompanySiret",
    "wasteDetailsQuantity",
    "quantityReceived",
    "wasteDetailsCode" as "wasteCode",
    "processingOperationDone" as "processing_operation_code",
    "status",
    "transporterTransportMode",
    "noTraceability",
    "wasteDetailsPop" as "wastePop"
 from
    "default$default"."Form" f
where
    ("emitterCompanySiret" = '{siret}'
    or "recipientCompanySiret" = '{siret}')
    and "isDeleted" = false
    and "createdAt" >= current_date - INTERVAL '1 year'
    and cast("status" as text) not in ('DRAFT', 'INITIAL', 'SIGNED_BY_WORKER')
order by
    "createdAt" asc
     