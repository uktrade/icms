__all__ = ["product_legislation"]

product_legislation = """
SELECT
  id
  , name
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , CASE is_biocidal WHEN 'true' THEN 1 ELSE 0 END is_biocidal
  , CASE is_eu_cosmetics_regulation WHEN 'true' THEN 1 ELSE 0 END is_eu_cosmetics_regulation
  , CASE is_biocidal_claim WHEN 'true' THEN 1 ELSE 0 END is_biocidal_claim
  , CASE gb_legislation WHEN 'true' THEN 1 ELSE 0 END gb_legislation
  , CASE ni_legislation WHEN 'true' THEN 1 ELSE 0 END ni_legislation
FROM impmgr.cert_app_product_legislation
ORDER BY id
"""
