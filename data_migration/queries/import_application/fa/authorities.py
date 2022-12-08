__all__ = [
    "fa_authorities",
    "fa_authority_linked_offices",
    "section5_authorities",
    "section5_clauses",
    "section5_linked_offices",
]

fa_authorities = """
SELECT iad.*, imp_id importer_id
FROM impmgr.importer_authorities ia
INNER JOIN (
  SELECT
    iad.ia_id id
    , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
    , x.*
  FROM impmgr.importer_authority_details iad,
    XMLTABLE('/*'
    PASSING iad.xml_data
    COLUMNS
      address VARCHAR2(4000) PATH '/AUTHORITY/ADDRESS/text()'
      , postcode VARCHAR2(4000) PATH '/AUTHORITY/POSTCODE/text()'
      , address_entry_type VARCHAR2(4000) PATH '/AUTHORITY/ADDRESS_ENTRY_TYPE/text()'
      , reference VARCHAR2(4000) PATH '/AUTHORITY/FIREARMS_REFERENCE/text()'
      , certificate_type VARCHAR2(4000) PATH '/AUTHORITY/CERTIFICATE_TYPE/text()'
      , further_details VARCHAR2(4000) PATH '/AUTHORITY/UNCATEGORIZED_DETAILS/text()'
      , issuing_constabulary_id INTEGER PATH '/AUTHORITY/ISSUING_CONSTABULARY/text()'
      , act_quantity_xml XMLTYPE PATH '/AUTHORITY/GOODS_CATEGORY_LIST'
      , file_folder_id INTEGER PATH '/AUTHORITY/DOCUMENTS_FF_ID/text()'
      , start_date VARCHAR2(4000) PATH '/AUTHORITY/START_DATE/text()'
      , end_date VARCHAR2(4000) PATH '/AUTHORITY/END_DATE/text()'
    ) x
  WHERE iad.status_control = 'C'
 ) iad ON iad.id = ia.id
 WHERE ia.authority_type = 'FIREARMS'
"""


fa_authority_linked_offices = """
SELECT
  ia_id firearmsauthority_id
  , 'i-' || imp_id || '-' || office_id office_legacy_id
FROM impmgr.xview_imp_auth_linked_offices xialo
INNER JOIN impmgr.importer_authorities ia ON xialo.ia_id = ia.id
WHERE status_control = 'C'
AND ia.authority_type = 'FIREARMS'
"""


section5_authorities = """
SELECT
  iad.*, imp_id importer_id
FROM impmgr.importer_authorities ia
INNER JOIN (
  SELECT
    iad.ia_id id
    , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
    , x.*
  FROM impmgr.importer_authority_details iad,
    XMLTABLE('/*'
    PASSING iad.xml_data
    COLUMNS
      address VARCHAR2(4000) PATH '/AUTHORITY/ADDRESS/text()'
      , postcode VARCHAR2(4000) PATH '/AUTHORITY/POSTCODE/text()'
      , address_entry_type VARCHAR2(4000) PATH '/AUTHORITY/ADDRESS_ENTRY_TYPE/text()'
      , reference VARCHAR2(4000) PATH '/AUTHORITY/SECTION5_REFERENCE/text()'
      , certificate_type VARCHAR2(4000) PATH '/AUTHORITY/CERTIFICATE_TYPE/text()'
      , further_details VARCHAR2(4000) PATH '/AUTHORITY/UNCATEGORIZED_DETAILS/text()'
      , clause_quantity_xml XMLTYPE PATH '/AUTHORITY/GOODS_CATEGORY_LIST'
      , file_folder_id INTEGER PATH '/AUTHORITY/DOCUMENTS_FF_ID/text()'
      , start_date VARCHAR2(4000) PATH '/AUTHORITY/START_DATE/text()'
      , end_date VARCHAR2(4000) PATH '/AUTHORITY/END_DATE/text()'
    ) x
  WHERE iad.status_control = 'C'
 ) iad ON iad.id = ia.id
 WHERE ia.authority_type = 'SECTION5'
"""


section5_clauses = """
SELECT
  name clause
  , mnemonic legacy_code
  , description
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , created_datetime
  , created_by_wua_id created_by_id
  , last_updated_datetime updated_datetime
  , last_updated_by_wua_id updated_by_id
FROM impmgr.section_5_clauses
"""


section5_linked_offices = """
SELECT
  ia_id section5authority_id
  , 'i-' || imp_id || '-' || office_id office_legacy_id
FROM impmgr.xview_imp_auth_linked_offices xialo
INNER JOIN impmgr.importer_authorities ia ON xialo.ia_id = ia.id
WHERE status_control = 'C'
AND ia.authority_type = 'SECTION5'
"""
