#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.urls import resolve, reverse

logger = logging.getLogger(__name__)


def url(view_name):
    """
        Reverse view name and return resolved url
    """
    if view_name:
        return reverse(view_name)

    return ""


def has_view_access(request, view_name):
    """
        Check if current user has access to given view
    """
    if not view_name:
        return True

    url = reverse(view_name)
    view = resolve(url).func.view_class()
    view.request = request
    return view.has_permission()


class MenuItem:
    """
        Base class for all menu items
    """

    def __init__(self, label=None):
        self.label = label

    def has_access(self, request):
        """
            Check if user has access to item
        """
        return True

    def as_html(self, request):
        return ""

    def html(self, request):
        if self.has_access(request):
            return self.as_html(request)

        return ""


class MenuLink(MenuItem):
    def __init__(self, label=None, view=None):
        super().__init__(label)
        self.view = view

    def has_access(self, request):
        return has_view_access(request, self.view)

    def as_html(self, request):
        return f"""
            <li class="top-menu-action">
              <a href="{url(self.view)}">{self.label}</a>
            </li>
        """


class MenuButton(MenuLink):
    def as_html(self, request):
        return f"""
            <li class="top-menu-button">
                <a href="{url(self.view) }" class="primary-button button" style="height:33px;line-height: 33px;">
                    {self.label}
                </a>
            </li>
        """


class SubMenuLink(MenuLink):
    def as_html(self, request):
        return f"""
            <li class="top-menu-subcategory-action">
                <a href="{url(self.view)}">{self.label}</a>
            </li>
        """


class SubMenu(MenuItem):
    def __init__(self, label=None, links=None):
        super().__init__(label)
        self.links = links

    def has_access(self, request):
        if not self.links:
            return True

        for link in self.links:
            if link.has_access(request):
                return True

        return False

    def as_html(self, request):
        links = ""
        for link in self.links or []:
            links += link.html(request)

        return f"""
            <li class="top-menu-subcategory">
                <span class="top-menu-subcategory-prompt">{self.label or ''}</span>
                <ul class="top-menu-subcategory-actions">
                    {links}
                </ul>
            </li>
        """


class MenuDropDown(MenuItem):
    def __init__(self, label=None, sub_menu_list=None):
        super().__init__(label)
        self.sub_menu_list = sub_menu_list

    def has_access(self, request):
        if not self.sub_menu_list:
            return True

        for sub_menu in self.sub_menu_list:
            if sub_menu.has_access(request):
                return True

        return False

    def as_html(self, request):
        sub_menu_items = ""
        for sub_menu in self.sub_menu_list or []:
            sub_menu_items += sub_menu.html(request)

        return f"""
            <li class="top-menu-dropdown">
                <a class="dropdown-label" href="#">{self.label}</a>
                <ul class="menu-out flow-down top-menu-subcategory-list">
                    {sub_menu_items}
                </ul>
            </li>
        """


class Menu:
    # TODO: note that the decision whether to show a view or not depends
    # entirely on each view referenced here being class-based view and a
    # subclass of PermissionRequiredMixin (see has_view_access, above).
    #
    # if we ever want to use function-based views for anything referenced from
    # here, implement a "check" argument for the Menu* classes, which is a
    # function used to call which returns True if the menu item should be shown
    # for the current user
    items = [
        MenuLink(label="Workbasket", view="workbasket"),
        MenuLink(label="Dashboard"),
        MenuLink(label="Reports"),
        MenuLink(label="Search Mailshots", view="mailshot-received"),
        MenuDropDown(
            label="Search",
            sub_menu_list=[
                SubMenu(
                    links=[
                        SubMenuLink(label="Search Import Applications"),
                        SubMenuLink(label="Search Certificate Applications"),
                    ]
                ),
            ],
        ),
        MenuDropDown(
            label="Admin",
            sub_menu_list=[
                SubMenu(
                    label="Importers/Exporters",
                    links=[
                        SubMenuLink(label="Importers", view="importer-list"),
                        SubMenuLink(label="Exporters", view="exporter-list"),
                    ],
                ),
                SubMenu(
                    label="Mailshot", links=[SubMenuLink(label="Mailshots", view="mailshot-list"),]
                ),
                SubMenu(
                    label="Reference Data",
                    links=[
                        SubMenuLink(label="Commodities", view="commodity-list"),
                        SubMenuLink(label="Constabularies", view="constabulary-list"),
                        SubMenuLink(label="Obsolete Calibres", view="obsolete-calibre-group-list"),
                        SubMenuLink(label="Section 5 Clauses", view="section5:list"),
                        SubMenuLink(label="Product legislation", view="product-legislation-list"),
                        SubMenuLink(label="Templates", view="template-list"),
                        SubMenuLink(label="Countries", view="country-list"),
                    ],
                ),
                SubMenu(
                    label="Users",
                    links=[SubMenuLink(label="Web User Accounts", view="users-list"),],
                ),
            ],
        ),
        MenuButton(label="New Import Application", view="new-import-application"),
        MenuButton(label="New Certificate Application", view="export:create"),
    ]

    def as_html(self, request):
        html = ""
        for item in self.items:
            html += item.html(request)
        return html
