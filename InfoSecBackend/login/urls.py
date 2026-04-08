from django.urls import path
from .views import LoginView, ResetPasswordView, RegisterView, GetAllUsersView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path("register/", RegisterView.as_view()),
    path("users/", GetAllUsersView.as_view(), name="get_all_users"),
]