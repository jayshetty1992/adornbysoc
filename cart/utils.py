from decimal import Decimal
from .models import Cart, CartItem


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()

    sk = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=sk)
    return cart


def cart_items_qs(cart):
    return cart.items.select_related("product").prefetch_related("product__images")


def cart_count(cart):
    # total qty (not number of unique items)
    return sum([it.qty for it in cart.items.all()])


def cart_subtotal(cart):
    items = cart.items.select_related("product")
    total = Decimal("0.00")
    for it in items:
        # assuming product.price_inr exists and is numeric
        total += Decimal(str(it.product.price_inr)) * it.qty
    return total


def first_product_image_url(product):
    # tries product.images related name; adjust if your related_name is different
    try:
        img = product.images.first()
        if img and getattr(img, "image", None) and getattr(img.image, "url", None):
            return img.image.url
        if img and getattr(img, "url", None):
            return img.url
    except Exception:
        pass
    return ""
