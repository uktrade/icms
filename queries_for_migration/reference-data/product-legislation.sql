--- Product legislation data to migrate over
SELECT
  capl.id AS pk
  , CASE WHEN capl.status='CURRENT' THEN 'True' ELSE 'False' END AS IS_ACTIVE
  , capl.name
  , CASE WHEN capl.IS_BIOCIDAL='true' THEN 'True' ELSE 'False' END AS IS_BIOCIDAL
  , CASE WHEN capl.IS_BIOCIDAL_CLAIM='true' THEN 'True' ELSE 'False' END AS IS_BIOCIDAL_CLAIM
  , CASE WHEN capl.IS_EU_COSMETICS_REGULATION='true' THEN 'True' ELSE 'False' END AS IS_EU_COSMETICS_REGULATION
  FROM impmgr.cert_app_product_legislation capl
