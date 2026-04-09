import math
from django.db.models import Count

from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from audit_log.models import AuditLog
from audit_log.middleware import get_client_ip
import uuid
import re
from django.contrib.auth.models import Group
from .serializers import UserAccessListItemSerializer, RoleListItemSerializer

ROLE_TO_PERMS = {
    "Admin": "All",
    "Staff": "Policies, Documents",
}

def build_user_payload(user):
    group_names = set(user.groups.values_list("name", flat=True))

    if user.is_superuser or "Admin" in group_names:
        role_name = "Admin"
    elif "Staff" in group_names:
        role_name = "Staff"
    else:
        role_name = "Staff"

    return {
        "user_id": str(user.pk),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": {
            "role_name": role_name,
            "permissions": ROLE_TO_PERMS.get(role_name, ""),
        },
    }


def build_user_access_payload(user):
    return {
        "user_id": str(user.pk),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "roles": list(user.groups.values_list("name", flat=True)),
        "last_login": user.last_login,
    }

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
            username=email,          # if default Django user
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        staff_group, _ = Group.objects.get_or_create(name="Staff")
        user.groups.add(staff_group)

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
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.prefetch_related("groups").all().order_by("id")

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
    permission_classes = [IsAdminUser]

    def get(self, request):
        roles = Group.objects.annotate(user_count=Count("user")).order_by("name")
        payload = [
            {
                "role_id": role.id,
                "role_name": role.name,
                "user_count": role.user_count,
            }
            for role in roles
        ]
        serializer = RoleListItemSerializer(payload, many=True)

        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)