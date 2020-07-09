from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# from rolepermissions.admin import RolePermissionsUserAdminMixin
from .models import User

# class UserRoleAdmin(RolePermissionsUserAdminMixin, UserAdmin):
#     pass

admin.site.register(User, UserAdmin)
