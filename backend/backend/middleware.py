import logging
import json

logger = logging.getLogger('backend.api_logger')

class ExcludeApiLogsFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # Restituisce False (ignora il log) se l'URL contiene /api/
        return not (' /api/' in msg)

class RequestLoggingMiddleware:
    """
    Middleware to log all incoming API requests and their payloads.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We only want to log API requests, ignoring admin and static files
        is_api = request.path.startswith('/api/')
        
        # Read payload before the request is processed
        payload = ""
        if is_api and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Read and decode the body
                body_unicode = request.body.decode('utf-8')
                
                # Attempt to format as JSON if possible for prettier logging
                if body_unicode:
                    try:
                        parsed = json.loads(body_unicode)
                        payload = json.dumps(parsed, indent=4)
                    except json.JSONDecodeError:
                        payload = body_unicode
            except Exception as e:
                payload = f"<Error reading payload: {e}>"

        # Let the rest of the Django stack process the request
        response = self.get_response(request)
        
        # Read the response payload
        response_payload = ""
        if is_api and hasattr(response, 'content'):
            try:
                content_unicode = response.content.decode('utf-8')
                if content_unicode:
                    try:
                        parsed_resp = json.loads(content_unicode)
                        response_payload = json.dumps(parsed_resp, indent=4)
                    except json.JSONDecodeError:
                        response_payload = content_unicode
            except Exception as e:
                response_payload = f"<Error reading response: {e}>"

        # Log after response is generated so we can include the status code
        if is_api:
            log_msg = f"[{request.method}] {request.get_full_path()} HTTP/1.1 | Status: {response.status_code}"
            if payload:
                log_msg += f"\nRequest Payload:\n{payload}\n"
            if response_payload:
                log_msg += f"\nResponse Payload:\n{response_payload}\n"
            
            # Log at INFO level
            logger.info(log_msg)

        return response
