ICMS V1 Teams
-------------

This document describes each team within ICMS v1.

Each team is a collection of roles that can be assigned to a user.

A "team" can have one of two scopes "UNIVERSAL_SET" or "PARENT".

UNIVERSAL_SET is a system level role, PARENT is an object level role.

Where an object level role is defined a "UREF_TYPE" value is given, This value indicates the object the role is associated with.

DEFAULT_SYSTEM_PRIV_LIST is a list of V1 permissions.

RESOURCE_TYPE_EDIT_LIST is a list of resources the role gives edit access to.

RESOURCE_TYPE_VIEW_LIST is a list of resource types the role gives view access to.

<!-- TOC -->
  * [ICMS V1 Teams](#icms-v1-teams)
  * [ILB Admin Users](#ilb-admin-users)
  * [ILB Search Users](#ilb-search-users)
  * [ILB Case Officers](#ilb-case-officers)
  * [Constabulary Contacts](#constabulary-contacts)
  * [Exporter Agent Contacts](#exporter-agent-contacts)
  * [Exporter Contacts](#exporter-contacts)
  * [ILB External Users](#ilb-external-users)
  * [Importer Agent Contacts](#importer-agent-contacts)
  * [Importer Contacts](#importer-contacts)
  * [ILB Support Users](#ilb-support-users)
  * [Reporting Super Users](#reporting-super-users)
  * [Reporting Category Management](#reporting-category-management)
  * [Reporting Team](#reporting-team)
  * [Workbasket Viewers](#workbasket-viewers)
  * [Country Super Users](#country-super-users)
<!-- TOC -->

----------------------------------------------------------------------------------------------------
ILB Admin Users
---------------
- RES_TYPE = IMP_ADMIN
- DESCRIPTION = People who maintain reference data for the system.
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE = 
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_ADMIN.xml)

**Roles:**

| Resource Co-ordinator    |                                                       |
|--------------------------|-------------------------------------------------------|
| Name                     | RESOURCE_COORDINATOR                                  |
| Description              | Has all permissions and can edit members of the team. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_REGULATOR<br/>CONTACTS_LHS                        |
| RESOURCE_TYPE_EDIT_LIST  |                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                       |

| Maintain All             |                                                                                                                                               |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Name                     | MAINTAIN_ALL                                                                                                                                  |
| Description              | Users can maintain all reference data for the system (importers, exporters, commodities, countries, categories etc).                          |
| DEFAULT_SYSTEM_PRIV_LIST | REGULATOR<br/>IMP_REGULATOR<br/>IMP_MAINTAIN_ALL<br/>MAILSHOT_ADMIN<br/>                                                                      |
| RESOURCE_TYPE_EDIT_LIST  | IMP_IMPORTER_CONTACTS<br/>IMP_IMPORTER_AGENT_CONTACTS<br/>IMP_EXPORTER_CONTACTS<br/>IMP_EXPORTER_AGENT_CONTACTS<br/>IMP_CONSTABULARY_CONTACTS |
| RESOURCE_TYPE_VIEW_LIST  | IMP_IMPORTER_CONTACTS<br/>IMP_IMPORTER_AGENT_CONTACTS<br/>IMP_EXPORTER_CONTACTS<br/>IMP_EXPORTER_AGENT_CONTACTS<br/>IMP_CONSTABULARY_CONTACTS |

| Dashboard User           |                                                            |
|--------------------------|------------------------------------------------------------|
| Name                     | DASHBOARD_USER                                             |
| Description              | Users can access the ICMS data dashboard.                  |
| DEFAULT_SYSTEM_PRIV_LIST | REGULATOR<br/>IMP_REGULATOR<br/>DASHBOARD_ACCESS_LHS<br/>  |
| RESOURCE_TYPE_EDIT_LIST  |                                                            |
| RESOURCE_TYPE_VIEW_LIST  |                                                            |

----------------------------------------------------------------------------------------------------
ILB Search Users
----------------
- RES_TYPE = IMP_ADMIN_SEARCH
- DESCRIPTION = ILB users who can search cases.
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE = 
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_ADMIN_SEARCH.xml)

**Roles:**

| Resource Co-ordinator    |                                                       |
|--------------------------|-------------------------------------------------------|
| Name                     | RESOURCE_COORDINATOR                                  |
| Description              | Has all permissions and can edit members of the team. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_REGULATOR<br/>CONTACTS_LHS                        |
| RESOURCE_TYPE_EDIT_LIST  |                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                       |

| Search Cases             |                                                                                                                              |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Name                     | SEARCH_CASES                                                                                                                 |
| Description              | Users can search across all cases.                                                                                           |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_REGULATOR<br/>IMP_SEARCH_CASES_LHS<br/>IMP_SEARCH_CASES_ALL<br/>IMP_CERT_SEARCH_CASES_LHS<br/>IMP_CERT_SEARCH_ALL_CASES  |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                                                              |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                                                              |

----------------------------------------------------------------------------------------------------
ILB Case Officers
-----------------
- RES_TYPE = IMP_CASE_OFFICERS
- DESCRIPTION = Case Officers of ILB.
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE = 
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_CASE_OFFICERS.xml)

**Roles:**

| Resource Co-ordinator    |                                                       |
|--------------------------|-------------------------------------------------------|
| Name                     | RESOURCE_COORDINATOR                                  |
| Description              | Has all permissions and can edit members of the team. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_REGULATOR<br/>CONTACTS_LHS<br/>REGULATOR<br/>     |
| RESOURCE_TYPE_EDIT_LIST  |                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                       |


| Import Application Case Officer  |                                                                                             |
|----------------------------------|---------------------------------------------------------------------------------------------|
| Name                             | CASE_OFFICER                                                                                |
| Description                      | Users in this role have the ability to process import application cases through the system. |
| DEFAULT_SYSTEM_PRIV_LIST         | IMP_REGULATOR<br/>IMP_CASE_OFFICER<br/>IMP_SEARCH_CASES_LHS<br/>IMP_SEARCH_CASES_ALL<br/>   |
| RESOURCE_TYPE_EDIT_LIST          |                                                                                             |
| RESOURCE_TYPE_VIEW_LIST          |                                                                                             |


| Certificate Application Case Officer  |                                                                                                      |
|---------------------------------------|------------------------------------------------------------------------------------------------------|
| Name                                  | CA_CASE_OFFICER                                                                                      |
| Description                           | Users in this role have the ability to process certificate application cases through the system.     |
| DEFAULT_SYSTEM_PRIV_LIST              | IMP_REGULATOR<br/>IMP_CERT_CASE_OFFICER<br/>IMP_CERT_SEARCH_CASES_LHS<br/>IMP_CERT_SEARCH_ALL_CASES  |
| RESOURCE_TYPE_EDIT_LIST               |                                                                                                      |
| RESOURCE_TYPE_VIEW_LIST               |                                                                                                      |

----------------------------------------------------------------------------------------------------
Constabulary Contacts
---------------------
- RES_TYPE = IMP_CONSTABULARY_CONTACTS
- DESCRIPTION = Constabulary Contacts
- SCOPED_WITHIN = PARENT
- UREF_TYPE = CON
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_CONSTABULARY_CONTACTS.xml)

**Roles:**

| Verified Firearms Authority Editor  |                                                                                                                        | Notes                                                                                                  |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Name                                | FIREARMS_AUTHORITY_EDITOR                                                                                              |                                                                                                        |
| Description                         | Users in this role have privileges to view and edit importer verified firearms authorities issued by the constabulary. |                                                                                                        |
| DEFAULT_SYSTEM_PRIV_LIST            | IMP_EDIT_FIREARMS_AUTHORITY<br/>IMP_REGULATOR                                                                          | IMP_REGULATOR privilege to ensure firearms authority editors access the system via the secure network  |
| RESOURCE_TYPE_EDIT_LIST             |                                                                                                                        |                                                                                                        |
| RESOURCE_TYPE_VIEW_LIST             |                                                                                                                        |                                                                                                        |

----------------------------------------------------------------------------------------------------
Exporter Agent Contacts
-----------------------
- RES_TYPE = IMP_EXPORTER_AGENT_CONTACTS
- DESCRIPTION = Agent exporters
- SCOPED_WITHIN = PARENT
- UREF_TYPE = EXP
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_EXPORTER_AGENT_CONTACTS.xml)

**Roles:**

| View Applications/Certificates  |                                                                                                          |
|---------------------------------|----------------------------------------------------------------------------------------------------------|
| Name                            | VIEW_APPLICATION                                                                                         |
| Description                     | Users in this role have the ability to view all applications and certificates for a particular exporter. |
| DEFAULT_SYSTEM_PRIV_LIST        | IMP_CERT_VIEW_APPLICATION<br/>IMP_CERT_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                           |
| RESOURCE_TYPE_EDIT_LIST         |                                                                                                          |
| RESOURCE_TYPE_VIEW_LIST         |                                                                                                          |

| Edit Applications        |                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------|
| Name                     | EDIT_APPLICATION                                                                      |
| Description              | Users in this role will be able to create and edit new applications for the exporter. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_CERT_EDIT_APPLICATION<br/>IMP_CERT_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT        |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                       |

----------------------------------------------------------------------------------------------------
Exporter Contacts
-----------------
- RES_TYPE = IMP_EXPORTER_CONTACTS
- DESCRIPTION = Exporters
- SCOPED_WITHIN = PARENT
- UREF_TYPE = EXP
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_EXPORTER_CONTACTS.xml)

**Roles:**

| View Applications/Certificates  |                                                                                                          |
|---------------------------------|----------------------------------------------------------------------------------------------------------|
| Name                            | VIEW_APPLICATION                                                                                         |
| Description                     | Users in this role have the ability to view all applications and certificates for a particular exporter. |
| DEFAULT_SYSTEM_PRIV_LIST        | IMP_CERT_VIEW_APPLICATION<br/>IMP_CERT_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                           |
| RESOURCE_TYPE_EDIT_LIST         |                                                                                                          |
| RESOURCE_TYPE_VIEW_LIST         |                                                                                                          |


| Edit Applications        |                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------|
| Name                     | EDIT_APPLICATION                                                                      |
| Description              | Users in this role will be able to create and edit new applications for the exporter. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_CERT_EDIT_APPLICATION<br/>IMP_CERT_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT        |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                       |

| Approve/Reject Agents and Exporters  |                                                                                                    |
|--------------------------------------|----------------------------------------------------------------------------------------------------|
| Name                                 | AGENT_APPROVER                                                                                     |
| Description                          | Users in this role will be able to approve and reject access for agents and new exporter contacts. |
| DEFAULT_SYSTEM_PRIV_LIST             | IMP_CERT_AGENT_APPROVER<br/>IMP_CERT_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                       |
| RESOURCE_TYPE_EDIT_LIST              |                                                                                                    |
| RESOURCE_TYPE_VIEW_LIST              |                                                                                                    |

----------------------------------------------------------------------------------------------------
ILB External Users
------------------
- RES_TYPE = IMP_EXTERNAL
- DESCRIPTION = External Users
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE = 
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_EXTERNAL.xml)

**Roles:**

| Resource Co-ordinator    |                                                       |
|--------------------------|-------------------------------------------------------|
| Name                     | RESOURCE_COORDINATOR                                  |
| Description              | Has all permissions and can edit members of the team. |
| DEFAULT_SYSTEM_PRIV_LIST | CONTACTS_LHS                                          |
| RESOURCE_TYPE_EDIT_LIST  |                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                       |

| Verified Section 5 Authority Editor  |                                                                                              | Notes                                                                                                  |
|--------------------------------------|----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Name                                 | SECTION5_AUTHORITY_EDITOR                                                                    |                                                                                                        |
| Description                          | Users in this role have privileges to view and edit importer verified section 5 authorities. |                                                                                                        |
| DEFAULT_SYSTEM_PRIV_LIST             | IMP_EDIT_SECTION5_AUTHORITY<br/>IMP_REGULATOR                                                | IMP_REGULATOR privilege to ensure section 5 authority editors access the system via the secure network |
| RESOURCE_TYPE_EDIT_LIST              |                                                                                              |                                                                                                        |
| RESOURCE_TYPE_VIEW_LIST              |                                                                                              |                                                                                                        |

----------------------------------------------------------------------------------------------------
Importer Agent Contacts
-----------------------
- RES_TYPE = IMP_IMPORTER_AGENT_CONTACTS
- DESCRIPTION = Agent importers
- SCOPED_WITHIN = PARENT 
- UREF_TYPE = IMP
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_IMPORTER_AGENT_CONTACTS.xml)

**Roles:**

| View Applications/Licences  |                                                                                                      |
|-----------------------------|------------------------------------------------------------------------------------------------------|
| Name                        | VIEW_APP                                                                                             |
| Description                 | Users in this role have the ability to view all applications and licences for a particular importer. |
| DEFAULT_SYSTEM_PRIV_LIST    | IMP_VIEW_APP<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                                         |
| RESOURCE_TYPE_EDIT_LIST     |                                                                                                      |
| RESOURCE_TYPE_VIEW_LIST     |                                                                                                      |

| Edit Applications        |                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------|
| Name                     | EDIT_APP                                                                              |
| Description              | Users in this role will be able to create and edit new applications for the importer. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_EDIT_APP<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                          |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                       |

| Vary Applications/Licences  |                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|
| Name                        | VARY_APP                                                                        |
| Description                 | Users in this role will be able to vary any licences for a particular importer. |
| DEFAULT_SYSTEM_PRIV_LIST    | IMP_VARY_APP<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                    |
| RESOURCE_TYPE_EDIT_LIST     |                                                                                 |
| RESOURCE_TYPE_VIEW_LIST     |                                                                                 |

----------------------------------------------------------------------------------------------------
Importer Contacts
-----------------
- RES_TYPE = IMP_IMPORTER_CONTACTS
- DESCRIPTION = Importers
- SCOPED_WITHIN = PARENT
- UREF_TYPE = IMP
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_IMPORTER_CONTACTS.xml)

**Roles:**

| View Applications/Licences  |                                                                                                      |
|-----------------------------|------------------------------------------------------------------------------------------------------|
| Name                        | VIEW_APP                                                                                             |
| Description                 | Users in this role have the ability to view all applications and licences for a particular importer. |
| DEFAULT_SYSTEM_PRIV_LIST    | IMP_VIEW_APP<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                                         |
| RESOURCE_TYPE_EDIT_LIST     |                                                                                                      |
| RESOURCE_TYPE_VIEW_LIST     |                                                                                                      |

| Edit Applications        |                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------|
| Name                     | EDIT_APP                                                                              |
| Description              | Users in this role will be able to create and edit new applications for the importer. |
| DEFAULT_SYSTEM_PRIV_LIST | IMP_EDIT_APP<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                          |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                       |

| Vary Applications/Licences  |                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|
| Name                        | VARY_APP                                                                        |
| Description                 | Users in this role will be able to vary any licences for a particular importer. |
| DEFAULT_SYSTEM_PRIV_LIST    | IMP_VARY_APP<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                    |
| RESOURCE_TYPE_EDIT_LIST     |                                                                                 |
| RESOURCE_TYPE_VIEW_LIST     |                                                                                 |

| Approve/Reject Agents and Importers  |                                                                                                    |
|--------------------------------------|----------------------------------------------------------------------------------------------------|
| Name                                 | AGENT_APPROVER                                                                                     |
| Description                          | Users in this role will be able to approve and reject access for agents and new importer contacts. |
| DEFAULT_SYSTEM_PRIV_LIST             | IMP_AGENT_APPROVER<br/>IMP_SEARCH_CASES_LHS<br/>MAILSHOT_RECIPIENT                                 |
| RESOURCE_TYPE_EDIT_LIST              |                                                                                                    |
| RESOURCE_TYPE_VIEW_LIST              |                                                                                                    |

----------------------------------------------------------------------------------------------------
ILB Support Users
-----------------
- RES_TYPE = IMP_SUPPORT
- DESCRIPTION = Support Users. 
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE = 
- [View Source](https://github.com/uktrade/icms-legacy/tree/master/ResourceTypes/IMP_SUPPORT.xml)

**Roles:**

| Resource Co-ordinator    |                                                       |
|--------------------------|-------------------------------------------------------|
| Name                     | RESOURCE_COORDINATOR                                  |
| Description              | Has all permissions and can edit members of the team. |
| DEFAULT_SYSTEM_PRIV_LIST | CONTACTS_LHS                                          |
| RESOURCE_TYPE_EDIT_LIST  |                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                       |

| Support User             |                                                                                                                                                                                                                          |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Name                     | SUPPORT_USER                                                                                                                                                                                                             |
| Description              | Users in this role have all ICMS system privileges.                                                                                                                                                                      |
| DEFAULT_SYSTEM_PRIV_LIST | REGULATOR<br/>IMP_REGULATOR<br/>IMP_CASE_OFFICER<br/>IMP_SEARCH_CASES_LHS<br/>IMP_SEARCH_CASES_ALL<br/>IMP_CERT_SEARCH_CASES_LHS<br/>IMP_CERT_SEARCH_ALL_CASES<br/>IMP_MAINTAIN_ALL<br/>MAILSHOT_ADMIN<br/>PEOPLE_SEARCH |
| RESOURCE_TYPE_EDIT_LIST  | IMP_IMPORTER_CONTACTS<br/>IMP_IMPORTER_AGENT_CONTACTS<br/>IMP_EXPORTER_CONTACTS<br/>IMP_EXPORTER_AGENT_CONTACTS<br/>IMP_CONSTABULARY_CONTACTS                                                                            |
| RESOURCE_TYPE_VIEW_LIST  | IMP_IMPORTER_CONTACTS<br/>IMP_IMPORTER_AGENT_CONTACTS<br/>IMP_EXPORTER_CONTACTS<br/>IMP_EXPORTER_AGENT_CONTACTS<br/>IMP_CONSTABULARY_CONTACTS                                                                            |

----------------------------------------------------------------------------------------------------
Reporting Super Users
---------------------
- RES_TYPE = REPORTING_SUPER_TEAM
- DESCRIPTION = This team provides roles for performing report related activities.
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE =

**Roles:**

| Team Coordinator         |                        |
|--------------------------|------------------------|
| Name                     | RESOURCE_COORDINATOR   |
| Description              | Administer this team.  |
| DEFAULT_SYSTEM_PRIV_LIST |                        |
| RESOURCE_TYPE_EDIT_LIST  |                        |
| RESOURCE_TYPE_VIEW_LIST  |                        |

| Report Administrator     |                                                                                                                                                       |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Name                     | REPORT_ADMINISTRATOR                                                                                                                                  |
| Description              | Users in this role can access the reports system using the left hand side of the workbasket both to search reporting teams and view/schedule reports. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                                                                                                                  |
| RESOURCE_TYPE_EDIT_LIST  | REPORTING_CATEGORY_MANAGEMENT<br/>REPORTING_TEAM                                                                                                      |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                                                                                       |

----------------------------------------------------------------------------------------------------
Reporting Category Management
-----------------------------
- RES_TYPE = REPORTING_CATEGORY_MANAGEMENT
- DESCRIPTION = This team provides roles with the ability to administer who has access to see users in a particular reporting category.
- SCOPED_WITHIN = PARENT
- UREF_TYPE = _RCAT

**Roles:**

| Team Coordinator         |                        |
|--------------------------|------------------------|
| Name                     | RESOURCE_COORDINATOR   |
| Description              | Administer this team.  |
| DEFAULT_SYSTEM_PRIV_LIST |                        |
| RESOURCE_TYPE_EDIT_LIST  |                        |
| RESOURCE_TYPE_VIEW_LIST  |                        |

| Report Administrator     |                                                                                                                                                                 |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Name                     | REPORT_TEAM_ADMINISTRATOR                                                                                                                                       |
| Description              | Users in this role can access the reports system using the left hand side of the workbasket to search reporting teams and edit which users have access to them. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                                                                                                                            |
| RESOURCE_TYPE_EDIT_LIST  | REPORTING_TEAM                                                                                                                                                  |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                                                                                                 |

| Report Scheduler         |                                                                                                                                                                                                                               |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Name                     | REPORT_SCHEDULER                                                                                                                                                                                                              |
| Description              | Users in this role have access to the reporting system to schedule reports either instantly, for future processing, or on a specific agenda. This is a powerful way of giving all scheduling privileges to experienced users. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                                                                                                                                                                                          |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                                                                                                                                                               |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                                                                                                                                                               |

----------------------------------------------------------------------------------------------------
Reporting Team
--------------
- RES_TYPE = REPORTING_TEAM
- DESCRIPTION = Members of this team will be allowed to view and schedule report runs.
- SCOPED_WITHIN = PARENT
- UREF_TYPE = _RPT
- Note: No RESOURCE_COORDINATOR as these teams should be looked after by the category administrator

**Roles:**

| Report Viewer            |                                                                     |
|--------------------------|---------------------------------------------------------------------|
| Name                     | REPORT_VIEWER                                                       |
| Description              | Users in this role gain access to view runs of a particular report. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                                |
| RESOURCE_TYPE_EDIT_LIST  |                                                                     |
| RESOURCE_TYPE_VIEW_LIST  |                                                                     |

| Instant Runner           |                                                       |
|--------------------------|-------------------------------------------------------|
| Name                     | REPORT_RUNNER_NOW                                     |
| Description              | Users in this role can run particular reports ad-hoc. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                  |
| RESOURCE_TYPE_EDIT_LIST  |                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                       |

| Schedule Runner          |                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------|
| Name                     | REPORT_RUNNER_LATER                                                                   |
| Description              | Users in this role can run particular reports scheduled for some point in the future. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                                                  |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                       |

| Repeat Runner            |                                                                                                            |
|--------------------------|------------------------------------------------------------------------------------------------------------|
| Name                     | REPORT_RUNNER_REPEAT                                                                                       |
| Description              | Users in this role can run particular reports which will be automatically reschedule on report completion. |
| DEFAULT_SYSTEM_PRIV_LIST | REPORTING_ACCESS_LHS                                                                                       |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                                            |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                                            |

----------------------------------------------------------------------------------------------------
Workbasket Viewers
------------------
- RES_TYPE = WORKBASKET_VIEW
- DESCRIPTION = Team for configuring access privileges to view other people's workbaskets
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE =

**Roles:**

| Team Coordinator            |                                                                                                                                        |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| Name                        | RESOURCE_COORDINATOR                                                                                                                   |
| Description                 | People in this role can edit this team. Warning... team coordinators will be able to add anyone to the team to view their workbasket.  |
| DEFAULT_SYSTEM_PRIV_LIST    |                                                                                                                                        |
| RESOURCE_TYPE_EDIT_LIST     |                                                                                                                                        |
| RESOURCE_TYPE_VIEW_LIST     |                                                                                                                                        |

| Workbasket Viewer        |                                                                                          |
|--------------------------|------------------------------------------------------------------------------------------|
| Name                     | WORKBASKET_VIEWER                                                                        |
| Description              | People in this role can view the workbasket of all people in the Workbasket Viewee role. |
| DEFAULT_SYSTEM_PRIV_LIST | WORKBASKET_VIEW_LHS                                                                      |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                          |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                          |

| Workbasket Viewee        |                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------|
| Name                     | WORKBASKET_VIEWEE                                                                     |
| Description              | People in this role can have their workbaskets viewed by people in the viewers role.  |
| DEFAULT_SYSTEM_PRIV_LIST |                                                                                       |
| RESOURCE_TYPE_EDIT_LIST  |                                                                                       |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                       |

----------------------------------------------------------------------------------------------------
Country Super Users
-------------------
- RES_TYPE = COUNTRY_SUPER_USERS
- DESCRIPTION = Users in this list have access to carry out the country maintenance
- SCOPED_WITHIN = UNIVERSAL_SET
- UREF_TYPE =

**Roles:**

| Team Coordinator         |                                                                        |
|--------------------------|------------------------------------------------------------------------|
| Name                     | RESOURCE_COORDINATOR                                                   |
| Description              | Only users in this list may change entries to this contact-list/team.  |
| DEFAULT_SYSTEM_PRIV_LIST |                                                                        |
| RESOURCE_TYPE_EDIT_LIST  |                                                                        |
| RESOURCE_TYPE_VIEW_LIST  |                                                                        |

| Country Set Super User   |                                                                                        |
|--------------------------|----------------------------------------------------------------------------------------|
| Name                     | COUNTRY_SET_SUPER_USER                                                                 |
| Description              | Users in this list are able to create online forms applications.                       |
| DEFAULT_SYSTEM_PRIV_LIST | COUNTRY_GROUP_CREATE<br/>COUNTRY_ADMIN_LHS<br/>COUNTRY_MANAGE<br/>COUNTRY_GROUP_MANAGE |
| RESOURCE_TYPE_EDIT_LIST  | COUNTRY_SET_ADMIN                                                                      |
| RESOURCE_TYPE_VIEW_LIST  |                                                                                        |
