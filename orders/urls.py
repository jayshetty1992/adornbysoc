from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("start/", views.checkout_start, name="checkout_start"),
    path("checkout/", views.checkout_view, name="checkout_view"),
    path("pay/<int:order_id>/", views.stripe_pay, name="stripe_pay"),
    path("create-intent/<int:order_id>/", views.create_payment_intent, name="create_payment_intent"),
    path("success/<int:order_id>/", views.success, name="success"),
    path("failed/<int:order_id>/", views.failed, name="failed"),
]
