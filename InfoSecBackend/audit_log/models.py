from django.db import models
import uuid

class AuditLog(models.Model):
    log_id = models.CharField(primary_key=True, max_length=255)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'audit_log'
        
    @staticmethod
    def generate_log_id():
        return f"LOG-{uuid.uuid4().hex[:8].upper()}"
