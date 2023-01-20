ICMS Features
================
Shown below are all the main pages and features in ICMS V1 and any relevant notes about them.

| Status                       | Notes                                                                     |
|------------------------------|---------------------------------------------------------------------------|
| Incomplete                   | Currently being worked on / missing core functionality                    |
| Complete                     | No further core work required (Does not include outstanding ILB feedback) |
| Complete (Needs revisiting)  | Feature complete but unknown if used correctly                            |
| Missing in V2                | Not implemented in v2 at all                                              |

| Feature / page                                                                                | ICMS V2 Status              | Notes                                                                              |
|-----------------------------------------------------------------------------------------------|-----------------------------|------------------------------------------------------------------------------------|
| [Workbasket](#workbasket)                                                                     | Incomplete                  |                                                                                    |
| [New Import Application](#new-import-application)                                             | Complete                    |                                                                                    |
| [New Certificate Application](#new-certificate-application)                                   | Complete                    |                                                                                    |
| [Case > Overview](#case--overview)                                                            | Complete                    |                                                                                    |
| [Case > Constabulary Emails](#case--constabulary-emails)                                      | Incomplete                  | All email needs revisiting                                                         |
| [Case > Sanction Emails](#case--sanction-emails)                                              | Incomplete                  | All email needs revisiting                                                         |
| [Case > HSE Emails](#case--hse-emails)                                                        | Incomplete                  | All email needs revisiting                                                         |
| [Case > BEIS Emails](#case--beis-emails)                                                      | Incomplete                  | All email needs revisiting                                                         |
| [Case > Variations](#case--variations)                                                        | Complete                    |                                                                                    |
| [Case > Application Withdrawals](#case--application-withdrawals)                              | Complete                    |                                                                                    |
| [Case > Application Updates](#case--application-updates)                                      | Complete                    |                                                                                    |
| [Case > Further Information Requests](#case--further-information-requests)                    | Complete                    |                                                                                    |
| [Case > Case Notes](#case--case-notes)                                                        | Complete                    |                                                                                    |
| [Case > Response Preparation](#case--response-preparation)                                    | Complete                    |                                                                                    |
| [Case > IMI Summary](#case--imi-summary)                                                      | Complete                    |                                                                                    |
| [Case > Authorisation](#case--authorisation)                                                  | Complete                    |                                                                                    |
| [Case > Access Approval](#case--access-approval)                                              | Complete                    |                                                                                    |
| [Case > Close Access Request](#case--close-access-request)                                    | Complete                    |                                                                                    |
| [Case > View Application](#case--view-application)                                            | Complete                    |                                                                                    |
| [Case > Responses](#case--responses)                                                          | Complete                    |                                                                                    |
| [Case > Issued Certificates](#case--issued-certificates)                                      | Complete                    |                                                                                    |
| [Document generation](#document-generation)                                                   | Incomplete                  | Only a few pdfs have been generated                                                |
| [Chief submission](#chief-submission)                                                         | Incomplete                  |                                                                                    |
| [Dashboard](#dashboard)                                                                       | Missing in V2               |                                                                                    |
| [Exporter Details](#exporter-details)                                                         | Missing in V2               |                                                                                    |
| [Importer Details](#importer-details)                                                         | Missing in V2               |                                                                                    |
| [Search > Search Import Applications](#search--search-import-applications)                    | Incomplete                  | Some actions have not been implemented                                             |
| [Search > Search Certificate Applications](#search--search-certificate-applications)          | Incomplete                  | Some actions have not been implemented                                             |
| [Search > Search Mailshots](#search--search-mailshots)                                        | Complete (needs revisiting) | Unknown if complete / used correctly                                               |
| [Search > Manage IMI cases](#search--manage-imi-cases)                                        | Complete                    |                                                                                    |
| [Admin >  CHIEF Dashboard](#admin--chief-dashboard)                                           | Incomplete                  | Some actions have not been implemented                                             |
| [Admin > Importers](#admin--importers)                                                        | Complete                    |                                                                                    |
| [Admin > Exporters](#admin--exporters)                                                        | Complete                    |                                                                                    |
| [Admin > Mailshots](#admin--mailshots)                                                        | Complete (needs revisiting) | Unknown if complete / used correctly                                               |
| [Admin > Reference Data > Commodities](#admin--reference-data--commodities)                   | Complete (needs revisiting) | Needs revisiting before go live                                                    |
| [Admin > Reference Data > Constabularies](#admin--reference-data--constabularies)             | Complete (needs revisiting) | Not known how constabulary emails fit in to ICMS                                   |
| [Admin > Reference Data > Sanction Emails](#admin--reference-data--sanction-emails)           | Complete (needs revisiting) | Not known how sanction emails fit in to ICMS                                       |
| [Admin > Reference Data > Obsolete Calibres](#admin--reference-data--obsolete-calibres)       | Complete (needs revisiting) | Not known if we need to migrate V2 obsolete calibre data                           |
| [Admin > Reference Data > Section 5 Clauses](#admin--reference-data--section-5-clauses)       | Complete (needs revisiting) | Not known if this data is used in V2 even though admin screen has been implemented |
| [Admin > Reference Data > Product Legislation](#admin--reference-data--product-legislation)   | Complete                    |                                                                                    |
| [Admin > Reference Data > Countries](#admin--reference-data--countries)                       | Incomplete                  | Need to investigate all uses of country data in the system                         |
| [Admin > Reference Data > Signatures](#admin--reference-data--signatures)                     | Missing in V2               |                                                                                    |
| [Admin > Templates](#admin--templates)                                                        | Incomplete                  | Needs investigation to all template uses in ICMS                                   |
| [Admin > Matrix Folders](#admin--matrix-folders)                                              | Missing in V2               | No idea if this is needed                                                          |
| [Admin > Teams](#admin--teams)                                                                | Incomplete                  | Needs revisiting - See section for more information                                |
| [Admin > Certificate Application Templates](#admin--certificate-application-templates)        | Incomplete                  | Doesn't feel like this should be a core v2 feature                                 |
| [\[Username\] > Request Importer/Exporter Access](#username--request-importerexporter-access) | Complete                    |                                                                                    |
| [\[Username\] > My Details](#username--my-details)                                            | Complete (needs revisiting) | Revisit when doing the Teams work                                                  |
| [\[Username\] > Logout](#username--logout)                                                    | Complete                    |                                                                                    |



Workbasket
----------
List view of all Import & Certificate applications and access requests.

From the workbasket a user can see relevant actions and links relating to applications they have permission to view.

e.g. An admin might see a "Manage" link, where as an application might see a "View Application" link.

New Import Application
----------------------
Main applicant page from which they can create import applications.

Types of application:
- Derogation from Sanctions Import Ban
- Firearms and Ammunition
    - Deactivated Firearms Licence
    - Open Individual Import Licence
    - Specific Individual Import Licence
- General Surveillance
- Iron and Steel (Quota)
- Outward Processing Trade
- Prior Surveillance
- Sanctions and Adhoc Licence Application
- Textiles (Quota)
- Wood (Quota)

New Certificate Application
---------------------------
Main applicant page from which they can create certificate applications.

Types of application:
- Certificate of Free Sale
- Certificate of Manufacture
- Certificate of Good Manufacturing Practice

Case > Overview
---------------
ILB caseworker screen for a particular import application, certificate application or access request.

Case > Constabulary Emails
--------------------------
ILB caseworker screen for a particular import application.

Case > Sanction Emails
----------------------
ILB caseworker screen for a particular import application.

Case > HSE Emails
-----------------
ILB caseworker screen for a particular certificate application.

Case > BEIS Emails
------------------
ILB caseworker screen for a particular certificate application.

Case > Variations
-----------------
ILB caseworker screen for a particular import or certificate application.

Case > Application Withdrawals
------------------------------
ILB caseworker screen for a particular import or certificate application.

Case > Application Updates
--------------------------
ILB caseworker screen for a particular import or certificate application.

Case > Further Information Requests
-----------------------------------
ILB caseworker screen for a particular import application, certificate application or access request.

Case > Case Notes
-----------------
ILB caseworker screen for a particular import or certificate application.

Case > Response Preparation
---------------------------
ILB caseworker screen for a particular import or certificate application.

Case > IMI Summary
------------------
ILB caseworker screen for a particular import application.

Case > Authorisation
--------------------
ILB caseworker screen for a particular import or certificate application.

Case > Access Approval
----------------------
ILB caseworker screen for a particular access request.

Case > Close Access Request
---------------------------
ILB caseworker screen for a particular access request.

Case > View Application
-----------------------
ILB caseworker screen for a particular import or certificate application.

Case > Responses
----------------
ILB caseworker screen for a particular import application.

This screen is only available when the application has been approved and completed.

Case > Issued Certificates
--------------------------
ILB caseworker screen for a particular certificate application.

This screen is only available when the application has been approved and completed.


Document generation
-------------------
Background process that happens after a case is authorised.

Import licence and export certificates get generated as PDFs and digitally signed.

Chief submission
----------------
Background process that happens after a case is authorised and the documents have been generated.

Import application data is serialised and send to HMRC via the CHIEF interface.

A licence is then either accepted or rejected.

Applications that are sent to CHIEF:
- Firearms and Ammunition
    - Deactivated Firearms Licence
    - Open Individual Import Licence
    - Specific Individual Import Licence
- Outward Processing Trade
- Sanctions and Adhoc Licence Application

Dashboard
---------
Page containing several reports:

- Import Applications Processed - last 6 month
- Certificate Requests Processed - last 6 month
- Outstanding Import Licence Requests Received Today
- Outstanding Certificate Requests Received Today
- Access Requests - today
- Access Requests - last 6 month
- Outstanding Import Licence Requests (broken down by current step in process)
- Outstanding Export Certificate Requests (broken down by current step in process)
- Outstanding Access Requests (broken down by current step in process)

Exporter Details
----------------
List view of all Exporters, presumably that the user has access to.

- This page isn't in V2
- The equivalent page in V2 accessible via the Maintain Exporters page (Admin > Exporters).
- It is not known if this list view of exporters is required in addition to the Admin "Maintain Exporters" page.

Importer Details
----------------
List view of all Importers, presumably that the user has access to.

- This page isn't in V2
- The equivalent page in V2 accessible via the Maintain Importers page (Admin > Importers).
- It is not known if this list view of importers is required in addition to the Admin "Maintain Importers" page.

Search > Search Import Applications
-----------------------------------
List view of historical import applications that is searchable.

Various actions can be shown here that affect the application.
Available actions:

- ~~Manage Appeals~~ - This has been removed as a feature in v2 (See closed story ICMSLST-1001 for details)
- Reassign caseworker
- Reopen Case
- Request Variation
- Revoke licence

Search > Search Certificate Applications
----------------------------------------
List view of historical certificate applications that is searchable.

Various actions can be shown here that affect the application.
Available actions:

- Copy Application
- Create Template
- Open Variation
- Reopen Case
- Revoke Certificates

Search > Search Mailshots
-------------------------
List view of Mailshots, includes a link to "view" a mailshot where more detailed information is shown

Search > Manage IMI cases
-------------------------
List view of IMI Cases, includes a link to "IMI Summary".
The IMI Summary lists all the information to be provided to the EU for a firearms case

Admin >  CHIEF Dashboard
------------------------
Shows applications that are currently being processed by CHIEF or have been rejected by CHIEF.

The available sub pages:

- Waiting on HMRC responses
- Pending Licences
- Failed Batches
- Failed Licences

In ICMS V2 this has been simplified to the following:
- Waiting on HRMC response
- Failed Licences

Admin > Importers
-----------------
Admin page with the following features to manage importers in ICMS:

- Search form to filter list of importers
- Link to "Create Main Importer" (Individual & Organisation)
- Link to "Search Access Requests"
- List view of Importers that have the following actions:
    - Edit Importer
        - Importer details
        - Add / edit / remove offices
        - Add / edit / remove Verified Firearms Authorities
        - Add / edit / remove Verified Section 5 Authorities
        - Add / edit / remove Agents
        - Add / edit / remove Contacts
            - Available contact permissions:
                - View Applications/Licences
                - Edit Applications
                - Vary Applications/Licences
                - Approve/Reject Agents and Importers
    - Add agent (Individual & Organisation)
    - Archive Importer

Admin > Exporters
-----------------
Admin page with the following features to manage exporters in ICMS:

- Search form to filter list of exporters
- Link to "Create Exporter"
- Link to "Search Access Requests"
- List view of exporters that have the following actions:
    - Edit exporter
        - exporter details
        - Add / edit / remove offices
        - Add / edit / remove Agents
        - Add / edit / remove Contacts
            - Available contact permissions:
                - View Applications/Certificates
                - Edit Applications
                - Approve/Reject Agents and Exporters
    - Create agent
    - Archive exporter

Admin > Mailshots
-----------------
Admin page with the following features to manage mailshots in ICMS:

- Search form to filter mailshots
- Link to "New Mailshot"
- List view of mailshots that have the following actions:
    - Edit
    - View
    - Retract

Admin > Reference Data > Commodities
------------------------------------
Admin page with the following features to manage commodities in ICMS:

- Create commodities
- Create commodity groups
- Search commodities
- Search commodity groups

Admin > Reference Data > Constabularies
---------------------------------------
Admin page with the following features to manage constabulary data in ICMS:

- Add a Constabulary
- Search constabularies
- Edit existing constabularies
- Delete existing constabularies

Admin > Reference Data > Sanction Emails
----------------------------------------
Admin page with the following features to manage sanction email data in ICMS:

- Add a sanction email
- Search sanction emails
- Edit existing sanction emails
- Delete existing sanction emails

Admin > Reference Data > Obsolete Calibres
------------------------------------------
Admin page with the following features to manage obsolete calibres in ICMS:

- Create obsolete calibres
- Create obsolete calibre groups
- Search obsolete calibres
- Search obsolete calibre groups
- Edit obsolete calibre and obsolete calibre groups

Admin > Reference Data > Section 5 Clauses
------------------------------------------
Admin page that lists all the section 5 clauses in ICMS, has the following features:

- Add a new section 5 clause
- Archive section 5 clause
- Unarchive section 5 clause
- Edit a section 5 clause

Admin > Reference Data > Product Legislation
--------------------------------------------
Admin page that lists all Product Legislation data in ICMS, has the following features:

- Filter legislation records
- Create a product legislation
- Edit a product legislation
- Archive a product legislation

Admin > Reference Data > Countries
----------------------------------
Admin page that has several features relating to countries, country groups and country translation sets in ICMS.

Countries are used in several places in ICMS, and we need to revisit this before going live.

There should be a distinct country group for every country select in ICMS, that way the system is configurable by the ILB team when we go live.

I have never looked in to what Country Translation Sets are used for and ICMS V2 does not currently use them in any way.

A quick look shows that it translates country names in to other languages, but I have never seen ICMS show these anywhere.

Maybe there is a language setting for  a user.

Features:
- Add New Country
- Manage Countries
- Add New Country Group
- Manage Country Groups
- Add Country Translations
- Manage Country Translation Sets

Admin > Reference Data > Signatures
-----------------------------------
Admin page for managing the signature that is used when creating licence / certificate pdfs.

Best described by the information banner in the V1 page:

_On this screen you can upload an image which will be used as a digital signature for all the application types. This also shows the list of the signatures used in the past with the validity period. You can only add one signature at the time._

Features:
- Upload a new signature
- Download existing / previous signatures
- View A PDF with the certificate on.

This page is present in ICMS V2.

Admin > Templates
-----------------
Admin page that can create many kinds of templates.

Types of template:
- CFS declaration translation
- CFS schedule
- CFS schedule translation
- CFS translation
- Declaration
- Email template
- Endorsement
- Letter fragment
- Letter template

ICMS V2 **_looks_** like it implements a lot of what we need from V1 but all the template work needs revisiting.

Just because we can create a template, is it used in the correct way?

Each type of template needs investigating and all places it is used needs defining before we revisit the implementation.

Admin > Matrix Folders
----------------------
I have no idea what this is, it is not implemented in V2.

Admin > Teams
-------------
Admin page for managing users in ICMS V1, best described by the information banner in the V1 page:

_Users can be put into teams. Each team has a different set of roles, and each user in the team can be given one or more roles. Adding a user to a role may give them extra system privileges. You can search all of the teams in the system below. You can leave 'Name' blank to list all teams._

ICMS V2 has a basic user permission system and needs revisiting.

The page to manage users in ICMS V2 can be found here: "Admin > Web User Accounts".

The V2 page was implemented very early in the build and needs a rewrite.

Admin > Certificate Application Templates
-----------------------------------------
Admin screen used by Exporter Users to create application templates which can be used to create certificate applications.

Can create the following application templates:
- Certificate of Free Sale
- Certificate of Manufacture
- Certificate of Good Manufacturing Practice

The templates can be private or shared with other users.

The ICMS V1 message that describes what sharing a certificate does:

_Whether or not other contacts of exporters/agents you are a contact of should be able view and create applications using this template, and if they can edit it._

\[Username\] > Request Importer/Exporter Access
-----------------------------------------------
Screen relevant to the logged-in user to request access to an Importer / Exporter or an agent of an Importer / Exporter

\[Username\] > My Details
-------------------------
Screen relevant to the logged-in user to amend user details.

This screen needs revisiting in V2 as it has a bug that changes the users password when updating user details .

\[Username\] > Logout
---------------------
Logs out the current logged-in user
