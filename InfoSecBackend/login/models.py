from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
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


class Role(models.Model):
    role_id = models.CharField(primary_key=True, max_length=255, default=uuid.uuid4, editable=False)
    role_name = models.CharField(max_length=255, unique=True)
    modules = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'role'

    def get_modules_list(self):
        if self.modules:
            return [module.strip() for module in self.modules.split(',') if module.strip()]
        return []


class UserManager(BaseUserManager):
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        if not username:
            username = email
        if not username:
            raise ValueError("The Username field must be set")

        email = self.normalize_email(email or username)
        user = self.model(username=username, email=email, **extra_fields)
        if not user.id:
            user.id = str(uuid.uuid4())
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username, email=email, password=password, **extra_fields)


class User(AbstractBaseUser):
    id = models.CharField(primary_key=True, max_length=255, default=uuid.uuid4, editable=False, db_column='user_id')
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='role_id',
        related_name='users',
    )
    # legacy fields removed to keep table similar to Django's auth_user
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username


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