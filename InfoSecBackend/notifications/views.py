from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
from django.contrib.auth import get_user_model
from notifications.models import UserNotification

# Create your views here.
class NotifView(APIView):
    def get(self, request):
        notifs = Notification.objects.all().order_by('-created_at')
        serializer = NotificationSerializer(notifs, many = True)
        print('(notifs dbg)', notifs)
        print("(debug) serializer data notifs ", serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user_model = get_user_model()
        curr_user = user_model.objects.get(id=request.data.get('curr_id'))
        UserNotification.objects.filter(to_user=curr_user).update(read=True)
