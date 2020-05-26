#!/usr/bin/env python
# -*- coding: utf-8 -*-
# NOQA: C0301

IMPORTER_ROLES = [{
    'name':
    'Importer Contacts:Approve/Reject Agents and Importers:{importer_id}',
    'description':
    'Users in this role will be able to approve and reject access for agents and new importer contacts.',
    'role_order':
    60,
    'permissions': [{
        'name':
        'Approve/Reject Agents and Importers',
        'codename':
        'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer_id}:IMP_AGENT_APPROVER'
    }, {
        'name':
        'Approve/Reject Agents and Importers',
        'codename':
        'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer_id}:IMP_SEARCH_CASES_LHS'
    }, {
        'name':
        'Approve/Reject Agents and Importers',
        'codename':
        'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer_id}:MAILSHOT_RECIPIENT'
    }, {
        'name':
        'Approve/Reject Agents and Importers',
        'codename':
        'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer_id}:MANAGE_IMPORTER_ACCOUNT'
    }]
}, {
    'name':
    'Importer Contacts:Edit Applications:{importer_id}',
    'description':
    'Users in this role will be able to create and edit new applications for the importer.',
    'role_order':
    40,
    'permissions': [{
        'name':
        'Edit Applications',
        'codename':
        'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer_id}:IMP_EDIT_APP'
    }, {
        'name':
        'Edit Applications',
        'codename':
        'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer_id}:IMP_SEARCH_CASES_LHS'
    }, {
        'name':
        'Edit Applications',
        'codename':
        'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer_id}:MAILSHOT_RECIPIENT'
    }, {
        'name':
        'Edit Applications',
        'codename':
        'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer_id}:MANAGE_IMPORTER_ACCOUNT'
    }]
}, {
    'name':
    'Importer Contacts:Vary Applications/Licences:{importer_id}',
    'description':
    'Users in this role will be able to vary any licences for a particular importer.',
    'role_order':
    50,
    'permissions': [{
        'name':
        'Vary Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VARY_APP:{importer_id}:IMP_SEARCH_CASES_LHS'
    }, {
        'name':
        'Vary Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VARY_APP:{importer_id}:IMP_VARY_APP'
    }, {
        'name':
        'Vary Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VARY_APP:{importer_id}:MAILSHOT_RECIPIENT'
    }, {
        'name':
        'Vary Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VARY_APP:{importer_id}:MANAGE_IMPORTER_ACCOUNT'
    }]
}, {
    'name':
    'Importer Contacts:View Applications/Licences:{importer_id}',
    'description':
    'Users in this role have the ability to view all applications and licences for a particular importer.',
    'role_order':
    30,
    'permissions': [{
        'name':
        'View Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VIEW_APP:{importer_id}:IMP_SEARCH_CASES_LHS'
    }, {
        'name':
        'View Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VIEW_APP:{importer_id}:IMP_VIEW_APP'
    }, {
        'name':
        'View Applications/Licences',
        'codename':
        'IMP_IMPORTER_CONTACTS:VIEW_APP:{importer_id}:MAILSHOT_RECIPIENT'
    }]
}]
