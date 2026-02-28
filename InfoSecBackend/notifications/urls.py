from django.urls import path
from .views import NotifView, send_notif, send_notif_batch
  
urlpatterns = [
    path('notifications/', NotifView.as_view(), name='notifications'),
    path('send-notif/', send_notif, name='send_notif'),
    path('send-notif-batch/', send_notif_batch, name='send_notif_batch')
    
]