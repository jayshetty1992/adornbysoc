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


def _run_shopify_sync():
    try:
        from django.core.management import call_command
        call_command("sync_shopify")
    except Exception:
        logging.getLogger(__name__).exception("shopify webhook sync failed")


@csrf_exempt
def shopify_webhook(request):
    """
    Shopify -> site auto-sync. Registered via `manage.py register_shopify_webhooks`
    for products/create, products/update and inventory_levels/update.
    Any such event re-syncs the catalog in the background, so product edits,
    archives and stock changes in Shopify admin reflect on the site within
    seconds — no manual sync needed.
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
    if topic.startswith("products/") or topic.startswith("inventory_levels/"):
        threading.Thread(target=_run_shopify_sync, daemon=True).start()
    return HttpResponse(status=200)
