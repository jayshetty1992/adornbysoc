from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from catalog.models import Product
from .models import CartItem
from .utils import get_cart, cart_items_qs, cart_subtotal, cart_count


def _sidebar_payload(request, cart):
    items = cart_items_qs(cart)
    subtotal = cart_subtotal(cart)
    count = cart_count(cart)

    html = render_to_string(
        "cart/_sidebar_cart.html",
        {"cart": cart, "items": items, "subtotal": subtotal, "count": count},
        request=request
    )
    return {"ok": True, "count": count, "subtotal": str(subtotal), "html": html}


# ✅ NOTE: cart_view removed (no cart.html page)


def add_to_cart(request, slug):
    cart = get_cart(request)
    product = get_object_or_404(Product, slug=slug, is_active=True)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.qty = min(99, item.qty + 1)
        item.save(update_fields=["qty"])

    # ✅ no cart.html redirect, just open homepage or go back
    return redirect(request.META.get("HTTP_REFERER", "/"))


def remove_from_cart(request, item_id):
    cart = get_cart(request)
    CartItem.objects.filter(cart=cart, id=item_id).delete()
    return redirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def update_qty(request, item_id):
    cart = get_cart(request)
    qty = int(request.POST.get("qty", "1") or "1")
    qty = max(1, min(99, qty))
    item = get_object_or_404(CartItem, cart=cart, id=item_id)
    item.qty = qty
    item.save(update_fields=["qty"])
    return redirect(request.META.get("HTTP_REFERER", "/"))


# =========================
# ✅ Sidebar endpoints
# =========================

def cart_sidebar(request):
    cart = get_cart(request)
    return JsonResponse(_sidebar_payload(request, cart))


def cart_count_api(request):
    cart = get_cart(request)
    return JsonResponse({"ok": True, "count": cart_count(cart)})


@require_POST
def ajax_add_to_cart(request, slug):
    cart = get_cart(request)
    product = get_object_or_404(Product, slug=slug, is_active=True)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.qty = min(99, item.qty + 1)
        item.save(update_fields=["qty"])

    return JsonResponse(_sidebar_payload(request, cart))


@require_POST
def ajax_remove_item(request, item_id):
    cart = get_cart(request)
    CartItem.objects.filter(cart=cart, id=item_id).delete()
    return JsonResponse(_sidebar_payload(request, cart))


@require_POST
def ajax_change_qty(request, item_id):
    cart = get_cart(request)
    action = (request.POST.get("action") or "").strip()  # inc / dec
    item = get_object_or_404(CartItem, cart=cart, id=item_id)

    if action == "inc":
        item.qty = min(99, item.qty + 1)
        item.save(update_fields=["qty"])
    elif action == "dec":
        item.qty = max(1, item.qty - 1)
        item.save(update_fields=["qty"])

    return JsonResponse(_sidebar_payload(request, cart))


@require_POST
def ajax_save_note(request):
    cart = get_cart(request)
    note = (request.POST.get("order_note") or "").strip()
    cart.order_note = note[:2000]
    cart.save(update_fields=["order_note"])
    return JsonResponse(_sidebar_payload(request, cart))
