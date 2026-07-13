from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="index"),
    path("page/<slug:slug>/", views.page, name="page"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("journal/", views.journal_list, name="journal_list"),
    path("journal/<slug:slug>/", views.journal_detail, name="journal_detail"),
]
