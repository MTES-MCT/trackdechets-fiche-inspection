SELECT
    id,
    "agrementNumber" AS "receiptNumber",
    department
FROM
    "default$default"."VhuAgrement"
WHERE
    id = '{id}'
