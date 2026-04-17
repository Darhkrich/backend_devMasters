from django.conf import settings
from rest_framework.versioning import BaseVersioning


class ProjectPathVersioning(BaseVersioning):
    def determine_version(self, request, *args, **kwargs):
        path_parts = [part for part in request.path.strip("/").split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] == "api":
            candidate = path_parts[1]
            if candidate in getattr(settings, "API_SUPPORTED_VERSIONS", ["v1"]):
                return candidate

        return getattr(settings, "API_DEFAULT_VERSION", "v1")
