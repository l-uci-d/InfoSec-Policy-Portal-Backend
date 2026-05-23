from django.core.exceptions import ValidationError
from django.db import models
import uuid

class UserStatus(models.TextChoices):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'

class UserType(models.TextChoices):
    EMPLOYEE = 'Employee'
    ADMIN = 'Admin'
    
class AccessLevel(models.IntegerChoices):
    READ_ONLY = 3, 'Read-Only'
    FULL_ACCESS = 10, 'Full Access'

class RolesPermission(models.Model):
    role_id = models.CharField(primary_key=True, max_length=255)
    role_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    permissions = models.TextField(null=True, blank=True)
    access_level = models.IntegerField(
        choices=AccessLevel.choices,
        default=AccessLevel.FULL_ACCESS,
    )
    
    class Meta:
        db_table = 'roles_permission'

    def clean(self):
        super().clean()
        if self.role_name and RolesPermission.objects.exclude(pk=self.pk).filter(role_name=self.role_name).exists():
            raise ValidationError({"role_name": "Role name already exists."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
        
    def get_modules_list(self):
        """Return the permissions as a list of module names"""
        if self.permissions:
            return [module.strip() for module in self.permissions.split(',')]
        return []

""" class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=255)
    employee_id = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    role = models.ForeignKey(
        RolesPermission,
        on_delete=models.CASCADE,
        db_column='role_id',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE
    )
    type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.EMPLOYEE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users' """