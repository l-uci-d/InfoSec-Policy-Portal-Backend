from django.urls import path
from .views import (
    LoginView,
    ResetPasswordView,
    RegisterView,
    GetAllUsersView,
    GetAllRolesView,
    CreateRoleView,
    GetRoleByNameView,
    GetCurrentUserRoleView,
    UpdateUserRolesView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path("register/", RegisterView.as_view()),
    path("users/", GetAllUsersView.as_view(), name="get_all_users"),
    path("roles/", GetAllRolesView.as_view(), name="get_all_roles"),
    path("roles/create/", CreateRoleView.as_view(), name="create_role"),
    path("roles/<str:role_name>/", GetRoleByNameView.as_view(), name="get_role_by_name"),
    path("users/me/role/", GetCurrentUserRoleView.as_view(), name="get_current_user_role"),
    path("users/roles/", UpdateUserRolesView.as_view(), name="update_user_roles"),
]