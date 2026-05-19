from django.urls import path
from .views import NotifView
  
urlpatterns = [
    path('notifications/', NotifView.as_view(), name='notifications'),
    
]