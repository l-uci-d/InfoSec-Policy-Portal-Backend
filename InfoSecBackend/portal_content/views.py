from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateformat import format as date_format
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from notifications.services import create_notif
from .models import PortalContent


def format_date(value):
    if not value:
        return ""

    local_value = timezone.localtime(value)
    return date_format(local_value, "M j, Y")


def portal_content_to_payload(content):
    updated_by_name = ""

    if content.updated_by:
        full_name = f"{content.updated_by.first_name} {content.updated_by.last_name}".strip()
        updated_by_name = full_name or content.updated_by.email

    return {
        "home": {
            "appDescription": content.app_description,
            "mission": content.mission,
            "vision": content.vision,
            "coreValues": content.core_values or [],
        },
        "recentNews": {
            "pinnedNotice": {
                "category": content.pinned_notice_category,
                "title": content.pinned_notice_title,
                "message": content.pinned_notice_message,
                "updatedAt": format_date(content.updated_at),
                "updatedBy": content.pinned_notice_author or updated_by_name,
            }
        },
    }


@api_view(["GET", "PUT"])
def portal_content_detail(request):
    content = PortalContent.get_solo()

    if request.method == "GET":
        return Response(portal_content_to_payload(content), status=status.HTTP_200_OK)

    data = request.data or {}

    home = data.get("home", {})
    recent_news = data.get("recentNews", {})
    pinned_notice = recent_news.get("pinnedNotice", {})

    old_pinned_notice = {
        "category": content.pinned_notice_category,
        "title": content.pinned_notice_title,
        "message": content.pinned_notice_message,
        "author": content.pinned_notice_author,
    }

    content.app_description = home.get("appDescription", content.app_description)
    content.mission = home.get("mission", content.mission)
    content.vision = home.get("vision", content.vision)

    core_values = home.get("coreValues", content.core_values)
    if isinstance(core_values, list) and len(core_values) > 0:
        content.core_values = core_values

    content.pinned_notice_category = pinned_notice.get(
        "category",
        content.pinned_notice_category,
    )

    content.pinned_notice_title = pinned_notice.get(
        "title",
        content.pinned_notice_title,
    )

    content.pinned_notice_message = pinned_notice.get(
        "message",
        content.pinned_notice_message,
    )

    content.pinned_notice_author = pinned_notice.get(
        "updatedBy",
        content.pinned_notice_author,
    )

    new_pinned_notice = {
        "category": content.pinned_notice_category,
        "title": content.pinned_notice_title,
        "message": content.pinned_notice_message,
        "author": content.pinned_notice_author,
    }

    pinned_notice_changed = old_pinned_notice != new_pinned_notice

    content.save()

    if pinned_notice_changed:
        actor = request.user if request.user.is_authenticated else None

        create_notif(
            actor=actor,
            action="updated pinned announcement",
            document=None,
            misc_title=content.pinned_notice_title,
        )

    return Response(portal_content_to_payload(content), status=status.HTTP_200_OK)