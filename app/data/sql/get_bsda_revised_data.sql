select id,
    "createdAt"
from "default$default"."BsdaRevisionRequest"
where "authoringCompanyId" = '{company_id}'
    and "createdAt" >= current_date - INTERVAL '1 year'