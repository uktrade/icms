#!/usr/bin/env python
# -*- coding: utf-8 -*-
# NOQA: C0301

IMPORTER_ROLES = [
    {
        "name": "Importer Contacts:Approve/Reject Agents and Importers:{id}",
        "description": "Users in this role will be able to approve and reject access for agents and new importer contacts.",
        "role_order": 60,
        "permissions": [
            "IMP_AGENT_APPROVER",
            "IMP_SEARCH_CASES_LHS",
            "MAILSHOT_RECIPIENT",
            "MANAGE_IMPORTER_ACCOUNT",
        ],
    },
    {
        "name": "Importer Contacts:Edit Applications:{id}",
        "description": "Users in this role will be able to create and edit new applications for the importer.",
        "role_order": 40,
        "permissions": [
            "IMP_EDIT_APP",
            "IMP_SEARCH_CASES_LHS",
            "MAILSHOT_RECIPIENT",
            "MANAGE_IMPORTER_ACCOUNT",
        ],
    },
    {
        "name": "Importer Contacts:Vary Applications/Licences:{id}",
        "description": "Users in this role will be able to vary any licences for a particular importer.",
        "role_order": 50,
        "permissions": [
            "IMP_VARY_APP",
            "IMP_SEARCH_CASES_LHS",
            "MAILSHOT_RECIPIENT",
            "MANAGE_IMPORTER_ACCOUNT",
        ],
    },
    {
        "name": "Importer Contacts:View Applications/Licences:{id}",
        "description": "Users in this role have the ability to view all applications and licences for a particular importer.",
        "role_order": 30,
        "permissions": ["IMP_VIEW_APP", "IMP_SEARCH_CASES_LHS", "MAILSHOT_RECIPIENT"],
    },
]
