from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "is_anonymous",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_anonymous",
        "is_staff",
        "is_active",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "UrbanEye Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "is_anonymous",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "UrbanEye Information",
            {
                "fields": (
                    "email",
                    "role",
                    "phone",
                    "is_anonymous",
                )
            },
        ),
    )