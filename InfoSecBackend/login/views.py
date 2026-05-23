import math
from django.db.models import Count

from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from audit_log.models import AuditLog
from audit_log.middleware import get_client_ip
import uuid
import re
from .models import Role, UserProfile
from .serializers import (
    UserAccessListItemSerializer,
    RoleListItemSerializer,
    RoleCreateRequestSerializer,
    RoleDetailSerializer,
    RoleModulesUpdateRequestSerializer,
    UserRoleBulkUpdateRequestSerializer,
    UserRoleUpdateResultSerializer,
)

ROLE_TO_MODULES = {
    "Admin": ["All"],
    "Staff": ["Policies", "Documents"],
}

DEFAULT_ROLE_NAME = "Staff"
ALL_MODULES_KEY = "All"
ADMIN_OVERRIDE_MODULE = "UserManagement" # if in role: {modules}, then considered as admin
APP_MODULES = ["Home", "Documents", "Policies", "RecentNews", "Others","UserManagement"]


def normalize_module_names(module_names):
    cleaned_modules = []
    seen = set()
    for module_name in module_names:
        module_name = (module_name or "").strip()
        if module_name and module_name in APP_MODULES and module_name not in seen:
            cleaned_modules.append(module_name)
            seen.add(module_name)
    return cleaned_modules


def get_custom_role_modules(role_name):
    role = Role.objects.filter(role_name=role_name).order_by("role_id").first()
    if not role:
        return None

    modules = role.get_modules_list()
    return normalize_module_names(modules)


def get_modules_for_role(role_name):
    custom_modules = get_custom_role_modules(role_name)
    if custom_modules is not None:
        return custom_modules

    modules = ROLE_TO_MODULES.get(role_name, [])
    if ALL_MODULES_KEY in modules:
        return [ALL_MODULES_KEY, *APP_MODULES]
    return modules


def get_modules_for_admin_check(role_name):
    modules = get_modules_for_role(role_name)
    if ALL_MODULES_KEY in modules:
        return APP_MODULES
    return modules


def is_effective_admin(group_names):
    if "Admin" in group_names:
        return True

    for role_name in group_names:
        if ADMIN_OVERRIDE_MODULE in get_modules_for_admin_check(role_name):
            return True

    return False


def build_roles_with_modules(role_names):
    return [
        {
            "role_name": role_name,
            "modules": get_modules_for_role(role_name),
        }
        for role_name in role_names
    ]


def get_user_role(user):
    profile = getattr(user, "profile", None)
    if profile and profile.role:
        return profile.role

    role_name = resolve_user_role_name(user)
    return Role.objects.filter(role_name=role_name).first()


def get_role_payload(role_name, role_id=None):
    return {
        "role_id": str(role_id or role_name),
        "role_name": role_name,
        "modules": get_modules_for_role(role_name),
    }


def resolve_user_role_name(user):
    profile = getattr(user, "profile", None)
    if profile and profile.role:
        return profile.role.role_name

    if user.is_superuser:
        return "Admin"
    return DEFAULT_ROLE_NAME


def build_user_payload(user):
    role = get_user_role(user)
    role_name = role.role_name if role else resolve_user_role_name(user)

    return {
        "user_id": str(user.pk),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": {
            "role_id": role.role_id if role else role_name,
            "role_name": role_name,
            "modules": role.get_modules_list() if role else get_modules_for_role(role_name),
        },
    }


def build_user_access_payload(user):
    role = get_user_role(user)
    role_name = role.role_name if role else resolve_user_role_name(user)
    return {
        "user_id": str(user.pk),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "roles": [get_role_payload(role_name, role.role_id if role else None)],
        "last_login": user.last_login,
    }


def build_role_detail_payload(role_name, role_id=None):
    return get_role_payload(role_name, role_id)


class GetCurrentUserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        effective_role = resolve_user_role_name(user)

        return Response({
            "success": True,
            "data": {
                "user_id": str(user.pk),
                "role": {
                    "role_name": effective_role,
                    "modules": get_modules_for_role(effective_role),
                },
                "available_modules": APP_MODULES,
            }
        }, status=status.HTTP_200_OK)


class GetRoleByNameView(APIView):
    permission_classes = []

    def get(self, request, role_name):
        role = Role.objects.filter(role_name=role_name).first()
        if role:
            payload = build_role_detail_payload(role.role_name, role.role_id)
        else:
            modules = get_modules_for_role(role_name)

            if not modules:
                return Response({
                    "success": False,
                    "message": "Role not found",
                }, status=status.HTTP_404_NOT_FOUND)

            payload = build_role_detail_payload(role_name)

        serializer = RoleDetailSerializer(payload)
        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)


class GetRolePermissionsView(APIView):

    def get(self, request, role_name):
        # modules come from custom Role or default mapping
        modules = get_modules_for_role(role_name)

        payload = {
            "role_name": role_name,
            "modules": modules,
            "django_permissions": [],
        }

        return Response({"success": True, "data": payload}, status=status.HTTP_200_OK)

User = get_user_model()

class LoginView(APIView):
    authentication_classes = []  # optional: allow unauthenticated
    permission_classes = []      # optional

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
            user_id=user.pk,
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

        staff_role, _ = Role.objects.get_or_create(
            role_name="Staff",
            defaults={"role_id": str(uuid.uuid4()), "modules": ", ".join(ROLE_TO_MODULES["Staff"])},
        )
        UserProfile.objects.update_or_create(user=user, defaults={"role": staff_role})

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
                status=400
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
        users = User.objects.all().order_by("id")

        paginator = UserPagination()
        paginated_users = paginator.paginate_queryset(users, request)

        payload = [build_user_access_payload(user) for user in paginated_users]

        serializer = UserAccessListItemSerializer(payload, many=True)

        # para sa frontend
        total_pages = math.ceil(paginator.page.paginator.count / paginator.page_size)

        return Response({
            "success": True,
            "data": serializer.data,
            "total_pages": total_pages
        }, status=status.HTTP_200_OK)


class GetAllRolesView(APIView):
    permission_classes = []

    def get(self, request):
        roles = Role.objects.annotate(user_count=Count("user_profiles")).order_by("role_name")
        payload = [
            {
                "role_id": role.role_id,
                "role_name": role.role_name,
                "user_count": role.user_count,
                "modules": role.get_modules_list(),
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
            role_id=str(uuid.uuid4()),
            role_name=role_name,
            modules=", ".join(modules),
        )

        payload = build_role_detail_payload(role.role_name, role.role_id)
        serializer = RoleDetailSerializer(payload)

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
        if role:
            role.modules = ", ".join(modules)
            role.save(update_fields=["modules"])
        else:
            role = Role.objects.create(
                role_id=str(uuid.uuid4()),
                role_name=role_name,
                modules=", ".join(modules),
            )

        payload = build_role_detail_payload(role_name, role.role_id)
        serializer = RoleDetailSerializer(payload)
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

        # if not role_names:
        #     return Response({
        #         "success": False,
        #         "message": "At least one non-empty role is required",
        #     }, status=status.HTTP_400_BAD_REQUEST)

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

        user_ids = [str(update["user_id"]) for update in updates]
        users = User.objects.filter(pk__in=user_ids)
        users_by_id = {str(user.pk): user for user in users}
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
                user_id = str(update["user_id"])
                user = users_by_id[user_id]
                selected_role_name = update["role"].strip()
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = roles_by_name[selected_role_name]
                profile.save(update_fields=["role"])

                # Keep auth flags aligned with explicit Admin group assignment.
                is_admin_role = selected_role_name == "Admin"
                if user.is_superuser != is_admin_role or user.is_staff != is_admin_role:
                    user.is_superuser = is_admin_role
                    user.is_staff = is_admin_role
                    user.save(update_fields=["is_superuser", "is_staff"])

                results.append({
                    "user_id": user_id,
                    "roles": [get_role_payload(selected_role_name, roles_by_name[selected_role_name].role_id)],
                })

        response_serializer = UserRoleUpdateResultSerializer(results, many=True)
        return Response({
            "success": True,
            "updated": response_serializer.data,
        }, status=status.HTTP_200_OK)