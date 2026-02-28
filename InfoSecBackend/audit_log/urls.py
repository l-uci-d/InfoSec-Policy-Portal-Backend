from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='logs')

urlpatterns = [
    path('logs/', include(router.urls)),
]