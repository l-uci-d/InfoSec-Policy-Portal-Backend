from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['log_id', 'user_id', 'action', 'timestamp', 'ip_address']
        read_only_fields = ['log_id', 'timestamp']