from django.db import connection
from .middleware import get_current_user, _thread_locals

class AuditConnection:
    """
    A context manager to set and unset the application user for database audit
    """
    def __enter__(self):
        # Get the current user from thread-local storage
        user_id = get_current_user()
        ip_address = getattr(_thread_locals, 'ip_address', None)
        
        if user_id:
            # Set the current user for the database session
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_user = %s", [user_id])
                
            if ip_address:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL app.client_ip = %s", [ip_address])
                    
        return connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset the current user
        with connection.cursor() as cursor:
            cursor.execute("RESET app.current_user")
            cursor.execute("RESET app.client_ip")