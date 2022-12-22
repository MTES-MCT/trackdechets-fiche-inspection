select id,
    "bsdaId" as "bsId",
    "createdAt"
from "default$default"."BsdaRevisionRequest"
where "authoringCompanyId" = '{company_id}'
    and "status"='ACCEPTED'
    and "createdAt" >= current_date - INTERVAL '1 year'