from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

import stripe

from cart.utils import get_cart, cart_items_qs, cart_subtotal
from .models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout_view(request):
    cart = get_cart(request)
    items = cart_items_qs(cart)

    # ✅ no cart.html redirect
    if not items.exists():
        return redirect("index")

    subtotal = cart_subtotal(cart)
    shipping = Decimal("0.00")
    total = subtotal + shipping

    # add line total for template usage
    enriched = []
    for it in items:
        line_total = Decimal(str(it.product.price_inr)) * it.qty
        it.line_total_inr = line_total
        enriched.append(it)

    if request.method == "POST":
        o = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=(request.POST.get("full_name") or "").strip(),
            phone=(request.POST.get("phone") or "").strip(),
            email=(request.POST.get("email") or "").strip(),
            address_line1=(request.POST.get("address1") or "").strip(),
            address_line2=(request.POST.get("address2") or "").strip(),
            city=(request.POST.get("city") or "").strip(),
            state=(request.POST.get("state") or "").strip(),
            pincode=(request.POST.get("pincode") or "").strip(),
            order_note=(request.POST.get("order_note") or "").strip() or cart.order_note,
            subtotal_inr=subtotal,
            shipping_inr=shipping,
            total_inr=total,
            status="created",
        )

        # snapshot items
        for it in items:
            OrderItem.objects.create(
                order=o,
                product_title=it.product.title,
                unit_price_inr=Decimal(str(it.product.price_inr)),
                qty=it.qty
            )

        return redirect("orders:stripe_pay", order_id=o.id)

    return render(
        request,
        "checkout/checkout.html",
        {
            "cart": cart,
            "items": enriched,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": total,
        }
    )


def stripe_pay(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "checkout/stripe_pay.html", {
        "order": order,
        "stripe_pk": settings.STRIPE_PUBLISHABLE_KEY
    })


@require_POST
def create_payment_intent(request, order_id):
    """
    Creates Stripe PaymentIntent and returns client_secret.
    """
    order = get_object_or_404(Order, id=order_id)

    if order.status != "created":
        return JsonResponse({"ok": False, "error": "Order is not payable."}, status=400)

    # Stripe amount in smallest currency unit: INR paisa
    amount_paise = int(Decimal(order.total_inr) * 100)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_paise,
            currency="inr",
            metadata={"order_id": str(order.id)},
            receipt_email=order.email,
        )

        order.stripe_payment_intent_id = intent["id"]
        order.stripe_client_secret = intent["client_secret"]
        order.save(update_fields=["stripe_payment_intent_id", "stripe_client_secret"])

        return JsonResponse({"ok": True, "client_secret": intent["client_secret"]})
    except Exception as e:
        order.status = "failed"
        order.save(update_fields=["status"])
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


def success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "checkout/success.html", {"order": order})


def failed(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "checkout/failed.html", {"order": order})


def checkout_start(request):
    """
    Single checkout entry point (the cart drawer links here).

    Shopify hosted checkout when it's fully configured AND every cart
    line is mapped to a Shopify variant; otherwise the legacy Stripe
    checkout. Misconfiguration can never take the store down.
    """
    from payments import shopify

    cart = get_cart(request)
    items = list(cart_items_qs(cart))
    if not items:
        return redirect("index")

    if shopify.enabled():
        lines = [(it.product.shopify_variant_gid, it.qty) for it in items]
        if all(gid for gid, _ in lines):
            try:
                return redirect(shopify.cart_checkout_url(lines, note=cart.order_note))
            except shopify.ShopifyError as e:
                import logging
                logging.getLogger(__name__).warning("Shopify checkout failed, using legacy: %s", e)
        else:
            import logging
            logging.getLogger(__name__).warning(
                "Shopify checkout skipped: cart has unmapped products (run sync_shopify)."
            )

    return redirect("orders:checkout_view")
