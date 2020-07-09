#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOQA: C0301

CONSTABULARY_ROLES = [
    {
        "name": "Constabulary Contacts:Verified Firearms Authority Editor:{id}",
        "description": "Users in this role have privileges to view and edit importer verified firearms authorities issued by the constabulary.",
        "role_order": 10,
        "permissions": ["IMP_EDIT_FIREARMS_AUTHORITY", "IMP_REGULATOR"],
    }
]
