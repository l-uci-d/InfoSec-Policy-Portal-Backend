from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import models


class Role(models.Model):
    role_id = models.CharField(primary_key=True, max_length=255)
    role_name = models.CharField(max_length=255, unique=True)
    modules = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "role"

    def clean(self):
        super().clean()
        if self.role_name and Role.objects.exclude(pk=self.pk).filter(role_name=self.role_name).exists():
            raise ValidationError({"role_name": "Role name already exists."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_modules_list(self):
        if self.modules:
            return [module.strip() for module in self.modules.split(",") if module.strip()]
        return []

    @property
    def permissions(self):
        return self.modules

    @permissions.setter
    def permissions(self, value):
        self.modules = value


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
        db_column="role_id",
    )

    class Meta:
        db_table = "user_profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        user_model = get_user_model()
        user_table = user_model._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE "{user_table}" SET role_id = %s WHERE id = %s',
                [self.role_id, self.user_id],
            )


RolesPermission = Role