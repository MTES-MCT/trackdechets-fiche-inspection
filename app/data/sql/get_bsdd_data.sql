select
    id,
    "createdAt",
    "sentAt",
    "receivedAt",
    "processedAt",
    "emitterCompanySiret",
    "recipientCompanySiret",
    "ownerId",
    "quantityReceived",
    "status"
 from
    "default$default"."Form" f
where
    "emitterCompanySiret" = '{siret}'
    or "recipientCompanySiret" = '{siret}'
    and "isDeleted" = false
    and "createdAt" >= current_date - INTERVAL '1 year'
     