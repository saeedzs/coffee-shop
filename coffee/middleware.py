from django.utils import translation


class EnglishAdminMiddleware:
    """The admin stays in English; only the public pages have both languages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        return self.get_response(request)
