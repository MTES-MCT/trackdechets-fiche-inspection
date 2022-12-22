select id,
    "bsddId" as "bsId",
    "createdAt"
from "default$default"."BsddRevisionRequest"
where "authoringCompanyId" = '{company_id}'
    and "status"='ACCEPTED'
    and "createdAt" >= current_date - INTERVAL '1 year'