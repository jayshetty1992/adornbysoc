# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from catalog.models import Collection, Product, ShopTheLook, ShopTheLookItem, ProductImage



def home(request):
    # Prefetch images so primary_image_obj / hover_image_obj works fast + correctly
    new_arrivals = (
        Product.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("sort_order", "id"))
        )
        .order_by("-created_at")[:10]
    )

    home_collections = (
        Collection.objects.filter(is_active=True, show_on_home=True)
        .only("id", "name", "slug", "card_image")
        .order_by("home_order", "name")[:12]
    )

    shop_look = None
    try:
        shop_look = (
            ShopTheLook.objects.filter(is_active=True)
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=ShopTheLookItem.objects.select_related("product").prefetch_related(
                        Prefetch("product__images", queryset=ProductImage.objects.order_by("sort_order", "id"))
                    ),
                )
            )
            .order_by("position", "-created_at")
            .first()
        )
    except Exception:
        shop_look = None

    return render(
        request,
        "index.html",
        {
            "new_arrivals": new_arrivals,
            "home_collections": home_collections,
            "shop_look": shop_look,
        },
    )


def page(request, slug):
    # basic CMS-like static pages (you can expand later)
    template_map = {
        "about": "pages/about.html",
        "contact": "pages/contact.html",
        "shipping": "pages/shipping.html",
        "returns": "pages/returns.html",
        "privacy": "pages/privacy.html",
    }
    tpl = template_map.get(slug, "pages/generic.html")
    return render(request, tpl, {"slug": slug})


@require_POST
def newsletter_subscribe(request):
    email = request.POST.get("email", "").strip()
    if email:
        # store in DB later; for now just flash
        messages.success(request, "Thanks! You are subscribed.")
    else:
        messages.error(request, "Please enter a valid email.")
    return redirect("home")
