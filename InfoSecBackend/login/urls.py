from django.urls import path
from .views import LoginView, check_email_exists, reset_password, check_password

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('check-email/', check_email_exists, name='check_email'),
    path('reset-password/', reset_password, name='reset_password'),
    path('check-password/', check_password, name='check_password' )
]