from django.urls import path
from . import views

urlpatterns = [
    path("create-intent/<int:order_id>/", views.create_payment_intent, name="create_payment_intent"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
    path("shopify/webhook/", views.shopify_webhook, name="shopify_webhook"),
]
