# admin/serializers.py
from rest_framework import serializers
from .models import User, RolesPermission

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolesPermission
        fields = ['role_id', 'role_name', 'description', 'permissions'] #'access_level']

class LoginResponseSerializer(serializers.ModelSerializer):
    # full_name = serializers.SerializerMethodField()
    # modules = serializers.SerializerMethodField()
    # access_level = serializers.SerializerMethodField()
    role = RoleSerializer()
    
    class Meta:
        model = User
        fields = '__all__'
        #fields = ['employee_id', 'full_name', 'email', 'modules', 'access_level']
        
    # def get_full_name(self, obj):
    #     return f"{obj.first_name} {obj.last_name}"
    
    # def get_modules(self, obj):
    #     if obj.role:
    #         return obj.role.get_modules_list()
    #     return []
    
    # def get_access_level(self, obj):
    #     if obj.role:
    #         return obj.role.access_level
    #     return None

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only = True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role"
        ]


class UserAccessListItemSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    roles = serializers.ListField(child=serializers.DictField())


class RoleListItemSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    role_name = serializers.CharField()
    user_count = serializers.IntegerField()
    modules = serializers.ListField(child=serializers.CharField())


class UserRoleUpdateItemSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    role = serializers.CharField(trim_whitespace=True, allow_blank=False)


class UserRoleBulkUpdateRequestSerializer(serializers.Serializer):
    updates = UserRoleUpdateItemSerializer(many=True, allow_empty=False)


class UserRoleUpdateResultSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    roles = serializers.ListField(child=serializers.DictField())


class RoleModuleSerializer(serializers.Serializer):
    role_name = serializers.CharField()
    modules = serializers.ListField(child=serializers.CharField())


class RoleCreateRequestSerializer(serializers.Serializer):
    role_name = serializers.CharField(trim_whitespace=True, allow_blank=False)
    modules = serializers.ListField(child=serializers.CharField(), allow_empty=False)


class RoleDetailSerializer(serializers.Serializer):
    role_id = serializers.CharField()
    role_name = serializers.CharField()
    modules = serializers.ListField(child=serializers.CharField())