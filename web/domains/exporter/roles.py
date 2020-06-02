#!/usr/bin/env python
# -*- coding: utf-8 -*-
# NOQA: C0301

EXPORTER_ROLES = [{
    'name':
    'Exporter Contacts:Approve/Reject Agents and Exporters:{id}',
    'description':
    'Users in this role will be able to approve and reject access for agents and new exporter contacts.',
    'role_order':
    60,
    'permissions': [
        'IMP_CERT_AGENT_APPROVER', 'IMP_CERT_SEARCH_CASES_LHS',
        'MAILSHOT_RECIPIENT'
    ]
}, {
    'name':
    'Exporter Contacts:Edit Applications:{id}',
    'description':
    'Users in this role will be able to create and edit new applications for the exporter.',
    'role_order':
    40,
    'permissions': [
        'IMP_CERT_EDIT_APPLICATION', 'IMP_CERT_SEARCH_CASES_LHS',
        'MAILSHOT_RECIPIENT'
    ]
}, {
    'name':
    'Exporter Contacts:View Applications/Certificates:{id}',
    'description':
    'Users in this role have the ability to view all applications and certificates for a particular exporter.',
    'role_order':
    30,
    'permissions': [
        'IMP_CERT_VIEW_APPLICATION', 'IMP_CERT_SEARCH_CASES_LHS',
        'MAILSHOT_RECIPIENT'
    ]
}]
