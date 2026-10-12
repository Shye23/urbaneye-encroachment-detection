
from django.contrib import admin
from .models import DangerZone


@admin.register(DangerZone)
class DangerZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "risk_level",
        "address",
        "is_active",
        "updated_at",
    )
    list_filter = (
        "risk_level",
        "is_active",
    )
    search_fields = (
        "name",
        "description",
        "address",
    )