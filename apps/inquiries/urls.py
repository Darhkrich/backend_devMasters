from django.urls import path

from .views import InquiryConvertToOrderView, InquiryDetailView, InquiryListCreateView

urlpatterns = [
    path("", InquiryListCreateView.as_view(), name="inquiry-list-create"),
    path("<int:pk>/", InquiryDetailView.as_view(), name="inquiry-detail"),
    path(
        "<int:pk>/convert/",
        InquiryConvertToOrderView.as_view(),
        name="inquiry-convert-to-order",
    ),
]
