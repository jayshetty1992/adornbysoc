import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_payment_intent(request, order_id):
    order = Order.objects.get(id=order_id)
    if not settings.STRIPE_SECRET_KEY:
        return JsonResponse({"error": "Stripe keys not configured"}, status=400)

    intent = stripe.PaymentIntent.create(
        amount=int(order.total_inr * 100),  # INR paise
        currency="inr",
        metadata={"order_id": str(order.id)},
        automatic_payment_methods={"enabled": True},
    )
    order.stripe_payment_intent_id = intent["id"]
    order.save(update_fields=["stripe_payment_intent_id"])
    return JsonResponse({"clientSecret": intent["client_secret"]})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)

    etype = event.get("type", "")
    obj = event.get("data", {}).get("object", {})
    order_id = (obj.get("metadata") or {}).get("order_id")

    if order_id:
        if etype == "payment_intent.succeeded":
            Order.objects.filter(id=order_id).update(status="paid")
        elif etype == "payment_intent.payment_failed":
            Order.objects.filter(id=order_id).update(status="failed")

    return HttpResponse(status=200)


# ---------- Shopify webhooks: auto-sync catalog when products change ----------

import base64
import hashlib
import hmac as hmac_mod
import logging
import os
import threading


def _run_shopify_order_sync():
    try:
        from payments import shopify_admin
        shopify_admin.sync_orders()
    except Exception:
        logging.getLogger(__name__).exception("shopify order sync failed")


@csrf_exempt
def shopify_webhook(request):
    """
    Shopify -> Django order sync. Registered via `manage.py
    register_shopify_webhooks` for orders/create + orders/updated: website
    orders (hosted checkout) appear in the Django dashboard within seconds
    and decrement local stock.
    """
    secret = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
    if not secret:
        return HttpResponse(status=503)

    digest = hmac_mod.new(secret.encode(), request.body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    given = request.META.get("HTTP_X_SHOPIFY_HMAC_SHA256", "")
    if not hmac_mod.compare_digest(expected, given):
        return HttpResponse(status=401)

    topic = request.META.get("HTTP_X_SHOPIFY_TOPIC", "")
    if topic.startswith("orders/"):
        threading.Thread(target=_run_shopify_order_sync, daemon=True).start()
    return HttpResponse(status=200)
