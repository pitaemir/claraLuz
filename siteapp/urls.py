from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("request/", views.request_lattes, name="request_lattes"),
    path("request/<str:public_id>/upload/", views.upload_docs, name="upload_docs"),
    path("request/<str:public_id>/finalize/", views.finalize_request, name="finalize_request"),
    path("sobre/", views.about, name="about"),
    path("ty/", views.thank_you, name="thank_you"),
]
