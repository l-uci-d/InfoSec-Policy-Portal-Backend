from django.conf import settings
from django.db import models


def default_core_values():
    return [
        "Integrity",
        "Accountability",
        "Confidentiality",
        "Security Awareness",
    ]


class PortalContent(models.Model):
    singleton_key = models.PositiveSmallIntegerField(
        default=1,
        unique=True,
        editable=False,
    )

    app_description = models.TextField(
        default=(
            "This portal provides a centralized space for viewing information "
            "security documents, managing policy-related content, and accessing "
            "department updates based on assigned user permissions."
        )
    )

    mission = models.TextField(
        default=(
            "To protect organizational information assets by promoting secure, "
            "reliable, and responsible use of technology across all departments."
        )
    )

    vision = models.TextField(
        default=(
            "To build a security-conscious organization where information protection "
            "is embedded in every system, process, and decision."
        )
    )

    core_values = models.JSONField(default=default_core_values)

    pinned_notice_category = models.CharField(
        max_length=100,
        default="Security Notice",
    )

    pinned_notice_title = models.CharField(
        max_length=255,
        default="Quarterly Security Awareness Campaign",
    )

    pinned_notice_message = models.TextField(
        default=(
            "The InfoSec Department will conduct a quarterly security awareness "
            "campaign covering phishing prevention, data handling, and safe access "
            "practices."
        )
    )

    pinned_notice_author = models.CharField(
        max_length=255,
        default="InfoSec Department",
        blank=True,
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="portal_content_updates",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portal_content"

    def __str__(self):
        return "Portal Home and News Content"

    @classmethod
    def get_solo(cls):
        content, _ = cls.objects.get_or_create(singleton_key=1)
        return content