from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.home, name="index"),
    path("page/<slug:slug>/", views.page, name="page"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("journal/", views.journal_list, name="journal_list"),
    path("journal/<slug:slug>/", views.journal_detail, name="journal_detail"),
]

# Reference page for the React island setup. Never routed in production.
if settings.DEBUG:
    urlpatterns += [
        path("dev/motion/", TemplateView.as_view(template_name="dev/motion.html"), name="dev_motion"),
    ]
