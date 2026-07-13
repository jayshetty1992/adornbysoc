from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="index"),
    path("page/<slug:slug>/", views.page, name="page"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
]
