# backend/middleware.py
from django.utils.cache import patch_cache_control

class NoStoreForAuthUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add headers for authenticated users
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            # Use Django helper so headers are well-formed
            patch_cache_control(response, no_store=True, no_cache=True, must_revalidate=True)
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response
