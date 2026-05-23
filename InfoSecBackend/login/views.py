import math
import re
import uuid

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Count
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit_log.middleware import get_client_ip
from audit_log.models import AuditLog
from .models import Role
from .serializers import (
    RoleCreateRequestSerializer,
    RoleDetailSerializer,
    RoleListItemSerializer,
    RoleModulesUpdateRequestSerializer,
    UserAccessListItemSerializer,
    UserRoleBulkUpdateRequestSerializer,
    UserRoleUpdateResultSerializer,
)

ROLE_TO_MODULES = {
    "Admin": ["All"],
    "Staff": ["Policies", "Documents"],
}

DEFAULT_ROLE_NAME = "Staff"
ALL_MODULES_KEY = "All"
APP_MODULES = ["Home", "Documents", "Policies", "RecentNews", "Others", "UserManagement"]

User = get_user_model()


def normalize_module_names(module_names):
    cleaned_modules = []
    seen = set()
    for module_name in module_names:
        module_name = (module_name or "").strip()
        if module_name and module_name in APP_MODULES and module_name not in seen:
            cleaned_modules.append(module_name)
            seen.add(module_name)
    return cleaned_modules


def get_or_create_default_role(role_name):
    raw_modules = ROLE_TO_MODULES.get(role_name, [])
    if ALL_MODULES_KEY in raw_modules:
        default_modules = [ALL_MODULES_KEY]
    else:
        default_modules = normalize_module_names(raw_modules)
    role, _ = Role.objects.get_or_create(
        role_name=role_name,
        defaults={"modules": ", ".join(default_modules)},
    )
    return role


def get_modules_for_role(role_name):
    role = Role.objects.filter(role_name=role_name).first()
    if role:
        raw_modules = role.get_modules_list()
        if ALL_MODULES_KEY in raw_modules:
            return [ALL_MODULES_KEY, *APP_MODULES]

        modules = normalize_module_names(raw_modules)
        if ALL_MODULES_KEY in modules:
            return [ALL_MODULES_KEY, *APP_MODULES]
        return modules

    modules = ROLE_TO_MODULES.get(role_name, [])
    if ALL_MODULES_KEY in modules:
        return [ALL_MODULES_KEY, *APP_MODULES]
    return modules


def build_roles_with_modules(role_names):
    return [
        {
            "role_name": role_name,
            "modules": get_modules_for_role(role_name),
        }
        for role_name in role_names
    ]


def resolve_user_role_name(user):
    if getattr(user, "is_superuser", False):
        return "Admin"

    role = getattr(user, "role", None)
    if role:
        return role.role_name

    return DEFAULT_ROLE_NAME


def build_user_payload(user):
    role_name = resolve_user_role_name(user)
    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": {
            "role_name": role_name,
            "modules": get_modules_for_role(role_name),
        },
    }


def build_user_access_payload(user):
    role_name = resolve_user_role_name(user)
    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "roles": build_roles_with_modules([role_name]),
        "last_login": user.last_login,
    }


def build_role_detail_payload(role):
    return {
        "role_id": str(role.role_id),
        "role_name": role.role_name,
        "modules": get_modules_for_role(role.role_name),
    }


class GetCurrentUserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role_name = resolve_user_role_name(user)

        return Response({
            "success": True,
            "data": {
                "id": str(user.id),
                "role": {
                    "role_name": role_name,
                    "modules": get_modules_for_role(role_name),
                },
                "available_modules": APP_MODULES,
            }
        }, status=status.HTTP_200_OK)


class GetRoleByNameView(APIView):
    permission_classes = []

    def get(self, request, role_name):
        role = Role.objects.filter(role_name=role_name).first()
        if not role:
            return Response({
                "success": False,
                "message": "Role not found",
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleDetailSerializer(build_role_detail_payload(role))
        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)


class GetRolePermissionsView(APIView):

    def get(self, request, role_name):
        role = Role.objects.filter(role_name=role_name).first()
        if not role:
            return Response({
                "success": False,
                "message": "Role not found",
            }, status=status.HTTP_404_NOT_FOUND)

        payload = {
            "role_name": role_name,
            "modules": get_modules_for_role(role_name),
            "django_permissions": [],
        }

        return Response({"success": True, "data": payload}, status=status.HTTP_200_OK)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        ip_address = get_client_ip(request)

        if not email or not password:
            AuditLog.objects.create(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                user_id=None,
                action="Failed login attempt: Missing credentials",
                ip_address=ip_address,
            )
            return Response({"success": False, "message": "Email and password are required"}, status=400)

        user = authenticate(request, username=email, password=password)
        if not user:
            AuditLog.objects.create(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                user_id=None,
                action=f"Failed login attempt for email: {email}",
                ip_address=ip_address,
            )
            return Response({"success": False, "message": "Invalid credentials"}, status=401)

        if not user.is_active:
            AuditLog.objects.create(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                user_id=user.pk,
                action="Login denied: Account is inactive",
                ip_address=ip_address,
            )
            return Response({"success": False, "message": "User account is inactive"}, status=403)

        AuditLog.objects.create(
            log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
            user_id=user.id,
            action="Successful login",
            ip_address=ip_address,
        )

        return Response({
            "success": True,
            "message": "Login successful",
            "data": build_user_payload(user)
        }, status=200)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        first_name = (request.data.get("first_name") or "").strip()
        last_name = (request.data.get("last_name") or "").strip()
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        confirm = request.data.get("confirm_password") or ""

        if not first_name or not last_name or not email or not password:
            return Response({"success": False, "message": "Missing fields"}, status=400)

        if password != confirm:
            return Response({"success": False, "message": "Passwords do not match"}, status=400)

        if not re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d).{8,}", password):
            return Response({"success": False, "message": "Password must be at least 8 characters and include letters and numbers"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"success": False, "message": "Email already registered. Login with that email or reset your password"}, status=409)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        staff_role = get_or_create_default_role(DEFAULT_ROLE_NAME)
        user.role = staff_role
        user.save(update_fields=["role"])

        return Response({
            "success": True,
            "message": "Registration successful",
            "data": build_user_payload(user)
        }, status=201)


class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        new_password = request.data.get("newPassword") or ""

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)

        if user.check_password(new_password):
            return Response(
                {"success": False, "message": "New password cannot be the same as your current password"},
                status=400,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"success": True})


class UserPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class GetAllUsersView(APIView):
    permission_classes = []

    def get(self, request):
        users = User.objects.select_related("role").all().order_by("id")

        paginator = UserPagination()
        paginated_users = paginator.paginate_queryset(users, request)

        payload = [build_user_access_payload(user) for user in paginated_users]
        serializer = UserAccessListItemSerializer(payload, many=True)

        total_pages = math.ceil(paginator.page.paginator.count / paginator.page_size)

        return Response({
            "success": True,
            "data": serializer.data,
            "total_pages": total_pages,
        }, status=status.HTTP_200_OK)


class GetAllRolesView(APIView):
    permission_classes = []

    def get(self, request):
        roles = Role.objects.annotate(user_count=Count("users")).order_by("role_name")
        payload = [
            {
                "role_id": str(role.role_id),
                "role_name": role.role_name,
                "user_count": role.user_count,
                "modules": get_modules_for_role(role.role_name),
            }
            for role in roles
        ]
        serializer = RoleListItemSerializer(payload, many=True)

        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)


class CreateRoleView(APIView):
    permission_classes = []

    def post(self, request):
        request_serializer = RoleCreateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        role_name = request_serializer.validated_data["role_name"]
        modules = normalize_module_names(request_serializer.validated_data["modules"])

        if not modules:
            return Response({
                "success": False,
                "message": "At least one valid module is required",
                "available_modules": APP_MODULES,
            }, status=status.HTTP_400_BAD_REQUEST)

        if Role.objects.filter(role_name=role_name).exists():
            return Response({
                "success": False,
                "message": "Role already exists",
            }, status=status.HTTP_409_CONFLICT)

        role = Role.objects.create(
            role_name=role_name,
            modules=", ".join(modules),
        )

        serializer = RoleDetailSerializer(build_role_detail_payload(role))
        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_201_CREATED)


class UpdateRoleModulesView(APIView):
    permission_classes = []

    def patch(self, request, role_name):
        request_serializer = RoleModulesUpdateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        modules = normalize_module_names(request_serializer.validated_data["modules"])
        if not modules:
            return Response({
                "success": False,
                "message": "At least one valid module is required",
                "available_modules": APP_MODULES,
            }, status=status.HTTP_400_BAD_REQUEST)

        role = Role.objects.filter(role_name=role_name).first()
        if not role:
            return Response({
                "success": False,
                "message": "Role not found",
            }, status=status.HTTP_404_NOT_FOUND)

        role.modules = ", ".join(modules)
        role.save(update_fields=["modules"])

        serializer = RoleDetailSerializer(build_role_detail_payload(role))
        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)


class UpdateUserRolesView(APIView):
    permission_classes = []

    def post(self, request):
        request_serializer = UserRoleBulkUpdateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        updates = request_serializer.validated_data["updates"]
        role_names = {
            update["role"].strip()
            for update in updates
            if update["role"].strip()
        }

        roles_by_name = {
            role.role_name: role
            for role in Role.objects.filter(role_name__in=role_names)
        }
        missing_roles = sorted(role_names - set(roles_by_name.keys()))
        if missing_roles:
            return Response({
                "success": False,
                "message": "Unknown role(s)",
                "unknown_roles": missing_roles,
            }, status=status.HTTP_400_BAD_REQUEST)

        user_ids = [str(update["id"]) for update in updates]
        users = User.objects.filter(id__in=user_ids).select_related("role")
        users_by_id = {str(user.id): user for user in users}
        missing_users = sorted(set(user_ids) - set(users_by_id.keys()))
        if missing_users:
            return Response({
                "success": False,
                "message": "Unknown user(s)",
                "unknown_users": missing_users,
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        with transaction.atomic():
            for update in updates:
                user_id = str(update["id"])
                user = users_by_id[user_id]
                selected_role_name = update["role"].strip()
                selected_role = roles_by_name[selected_role_name]

                user.role = selected_role
                is_admin_role = selected_role_name == "Admin"
                user.is_superuser = is_admin_role
                user.is_staff = is_admin_role
                user.save(update_fields=["role", "is_superuser", "is_staff"])

                results.append({
                    "id": user_id,
                    "roles": build_roles_with_modules([selected_role_name]),
                })

        response_serializer = UserRoleUpdateResultSerializer(results, many=True)
        return Response({
            "success": True,
            "updated": response_serializer.data,
        }, status=status.HTTP_200_OK)