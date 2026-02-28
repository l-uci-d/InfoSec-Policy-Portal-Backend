from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from .models import AuditLog
from .serializers import AuditLogSerializer
from rest_framework.decorators import action

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    http_method_names = ['get']
    
    # Add built-in search and ordering filters
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['log_id', 'user_id', 'action', 'ip_address']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']  # Default ordering by timestamp descending