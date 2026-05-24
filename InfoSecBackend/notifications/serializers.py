from rest_framework import serializers
from .models import Notification
from portal_content.models import PortalContent

class NotificationSerializer(serializers.ModelSerializer):
    document_title = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()

    def get_document_title(self, obj):
        if obj.document:
            return obj.document.title

        return obj.misc_title or "Pinned announcement"

    def get_actor_name(self, obj):
        action = (obj.action or "").lower()

        if obj.actor:
            full_name = f"{obj.actor.first_name} {obj.actor.last_name}".strip()

            if full_name:
                return full_name

            return getattr(obj.actor, "email", None) or "System"

        if (
            "pin" in action
            or "announcement" in action
            or "notice" in action
        ):
            portal_content = PortalContent.get_solo()
            return portal_content.pinned_notice_author or "InfoSec Department"

        return "System"

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor",
            "action",
            "document",
            "created_at",
            "document_title",
            "actor_name",
            "misc_title",
        ]