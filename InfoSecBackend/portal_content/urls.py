from django.urls import path
from .views import portal_content_detail

urlpatterns = [
    path("portal-content/", portal_content_detail, name="portal_content_detail"),
]