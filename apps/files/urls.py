from django.urls import path

from .views import ProjectFileViewSet


file_list_create = ProjectFileViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)
file_detail = ProjectFileViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
        "put": "update",
        "delete": "destroy",
    }
)
file_download = ProjectFileViewSet.as_view({"get": "download"})


urlpatterns = [
    path("", file_list_create, name="file-list-create"),
    path("<int:pk>/", file_detail, name="file-detail"),
    path("<int:pk>/download/", file_download, name="file-download"),
]
