# middleware.py
from django.utils.deprecation import MiddlewareMixin

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Get the IP address of the sender
        ip_address = self.get_client_ip(request)
        if not self.should_skip_logging(request.path):
        # Create log string
            log_message = f"{request.method} {request.path} from {ip_address}\n"

            # Save log to requestslogs.txt
            with open('requestslogs.txt', 'a') as log_file:
                log_file.write(log_message)

    def should_skip_logging(self, path):
        # Check if the path should be skipped from logging
        return path.startswith('/products') or path.startswith('/catalog') or path.startswith('/static') or path.startswith('/media')


    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_REAL_IP')
        if x_forwarded_for:
            # Use the first IP in the list, as it's the original client's IP
            ip = x_forwarded_for.split(',')[0]
        else:
            # If the X-Forwarded-For header is not present, fall back to REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR')
        return ip


