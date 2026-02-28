# admin/views.py
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import LoginResponseSerializer
from audit_log.models import AuditLog
from audit_log.middleware import get_client_ip
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model




class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        print("EMAIL: " + email)
        print("PASSWORD: " + password)

        # client IP for audit log
        ip_address = get_client_ip(request)
        
        if not email or not password:
            # Log failed login attempt with empty credentials
            log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
            AuditLog.objects.create(
                log_id=log_id,
                user_id=None,
                action=f"Failed login attempt: Missing credentials",
                ip_address=ip_address
            )

            return Response({
                'success': False,
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # verify user credentials
        # password is hashed using pgcrypto
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM admin.users WHERE email = %s AND password = crypt(%s, password)",
                [email, password]
            )
            row = cursor.fetchone()
        
        if not row:
            # log failed login attempt
            log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
            AuditLog.objects.create(
                log_id=log_id,
                user_id=None,
                action=f"Failed login attempt for email: {email}",
                ip_address=ip_address
            )

            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # get the column names from the cursor description
        columns = [col[0] for col in cursor.description]
        user_data = dict(zip(columns, row))
        
        # convert raw data to User instance for the serializer
        user = User(
            user_id=user_data['user_id'],
            employee_id=user_data.get('employee_id'),
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            password=user_data['password'],    # might need this if we'll implement password change
            status=user_data['status'],
            type=user_data['type'],
        )
        
        # if the user has a role, fetch that role's data
        if user_data.get('role_id'):
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM admin.roles_permission WHERE role_id = %s",
                    [user_data['role_id']]
                )
                role_row = cursor.fetchone()
                
                if role_row:
                    role_columns = [col[0] for col in cursor.description]
                    role_data = dict(zip(role_columns, role_row))
                    
                    # create a RolesPermission instance and attach it to the user
                    from .models import RolesPermission
                    role = RolesPermission(
                        role_id=role_data['role_id'],
                        role_name=role_data.get('role_name'),
                        description=role_data.get('description'),
                        permissions=role_data.get('permissions'),
                        access_level=role_data.get('access_level')
                    )
                    user.role = role
        
        # check if user is active
        if user.status != 'Active':
            # log failed login for inactive account
            log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
            AuditLog.objects.create(
                log_id=log_id,
                user_id=user.user_id,
                action=f"Login denied: Account is inactive",
                ip_address=ip_address
            )

            return Response({
                'success': False,
                'message': 'User account is inactive'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # log successful login
        log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
        AuditLog.objects.create(
            log_id=log_id,
            user_id=user.user_id,
            action=f"Successful login",
            ip_address=ip_address
        )
        
        # serialize the user data for the response
        serializer = LoginResponseSerializer(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
        

@csrf_exempt
def check_email_exists(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM admin.users WHERE email = %s LIMIT 1", [email])
            result = cursor.fetchone()

        if result:
            return JsonResponse({'exists': True})
        else:
            return JsonResponse({'exists': False})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        new_password = data.get('newPassword')

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE admin.users
            SET password = crypt(%s, gen_salt('bf', 06))
            WHERE email = %s;
        """, [new_password, email])
        
    return JsonResponse({"success": True})
@csrf_exempt
def check_password(request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')
    if request.method == 'POST':
        res = None
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM admin.users WHERE email = %s AND
                                                password = crypt(%s, password)
            """, [email, password])
            res = cursor.fetchone()
        
        if not res:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return JsonResponse({"success": True})
