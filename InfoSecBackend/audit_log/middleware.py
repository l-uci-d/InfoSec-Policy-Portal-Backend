import threading

# Thread-local storage to store the current user
_thread_locals = threading.local()

def get_current_user():
    """
    Return the current user from thread-local storage
    """
    return getattr(_thread_locals, 'user', None)

def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clear any existing user
        _thread_locals.user = None
        
        # Check if user is authenticated in request (from session or token)
        if hasattr(request, 'user') and request.user.is_authenticated:
            _thread_locals.user = request.user.user_id
        
        # Also check for user_id in request headers (for API calls)
        elif 'HTTP_X_USER_ID' in request.META:
            _thread_locals.user = request.META.get('HTTP_X_USER_ID')
            
        # Store client IP address
        _thread_locals.ip_address = get_client_ip(request)
            
        response = self.get_response(request)
        return response