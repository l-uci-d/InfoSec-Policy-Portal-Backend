from django.contrib import admin
from .models import PortalContent


@admin.register(PortalContent)
class PortalContentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pinned_notice_title",
        "pinned_notice_author",
        "updated_at",
    )

    readonly_fields = ("updated_at",)