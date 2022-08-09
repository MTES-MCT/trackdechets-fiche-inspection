select id,
    "createdAt"
from "default$default"."BsddRevisionRequest" brr
where "authoringCompanyId" = '{company_id}'
    and "createdAt" >= current_date - INTERVAL '1 year'