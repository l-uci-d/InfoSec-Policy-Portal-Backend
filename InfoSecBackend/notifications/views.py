from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

# Create your views here.
class NotifView(APIView):
    def get(self, request):
        
        req_user_id = str(request.query_params.get('user_id'))
        print(f'(notifs dbg) Notif view get with user id {req_user_id}')
        print(f'(notifs dbg) user_id type: {type(req_user_id)}, value: {repr(req_user_id)}')
        notifs = Notification.objects.filter(to_user_id=req_user_id.strip()).order_by('-created_at')
        print(f'(notifs dbg) generated query: {notifs.query}')
        serializer = NotificationSerializer(notifs, many = True)
        print('(notifs dbg)', notifs)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        notif_id = request.data.get('notifications_id')
        notif = Notification.objects.get(notifications_id=notif_id)
        notif.notifications_status = 'Read'
        notif.save()
        return Response({
            'success': True,
        }, status=status.HTTP_200_OK)
    
@csrf_exempt
def send_notif(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print('Creating notif...')
        origin_module =  data.get('module')
        origin_submodule = data.get('submodule')
        recipient_id = data.get('recipient_id')
        msg = data.get('msg')
        origin_string = origin_module
        if origin_submodule:
            origin_string += '/' + origin_submodule
        print(f'({origin_string}, {recipient_id}, {msg})')
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO admin.notifications (module, to_user_id, message, notifications_status, created_at)
                VALUES
                    (%s, %s, %s, 'Unread', NOW());
            """, [origin_string, recipient_id, msg])
    return JsonResponse({"success": True})

@csrf_exempt
def send_notif_batch(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print('Creating notifs...')
        origin_module =  data.get('module')
        origin_submodule = data.get('submodule')
        recipient_ids = data.get('recipient_ids')
        msg = data.get('msg')
        origin_string = origin_module
        if origin_submodule:
            origin_string += '/' + origin_submodule

        values_query = ''
        args = []

        for i in range(len(recipient_ids)):
            values_query += "(%s, %s, %s, 'Unread', NOW())"
            if (i < len(recipient_ids)-1):
                values_query += ",\n"
            args.append(origin_string)
            args.append(recipient_ids[i])
            args.append(msg)
            print(f'({origin_string}, {recipient_ids[i]}, {msg})')
            
        print(values_query)
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO admin.notifications (module, to_user_id, message, notifications_status, created_at)
                VALUES
                """
                + values_query + ";"
            , args)

    return JsonResponse({"success": True})
 