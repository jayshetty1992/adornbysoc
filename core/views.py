# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from catalog.models import Collection, Product, ShopTheLook, ShopTheLookItem, ProductImage, ProductReview, JournalPost



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

    base = Product.objects.filter(is_active=True).prefetch_related(
        Prefetch("images", queryset=ProductImage.objects.order_by("sort_order", "id"))
    )
    bestsellers = base.filter(in_stock=True, old_price_inr__isnull=True).order_by("price_inr")[:10]
    on_sale = base.filter(old_price_inr__isnull=False).order_by("-created_at")[:10]

    reviews = (
        ProductReview.objects.filter(is_approved=True)
        .select_related("product")
        .order_by("-created_at")[:8]
    )

    return render(
        request,
        "index.html",
        {
            "new_arrivals": new_arrivals,
            "home_collections": home_collections,
            "shop_look": shop_look,
            "reviews": reviews,
            "bestsellers": bestsellers,
            "on_sale": on_sale,
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
        "warranty": "pages/warranty.html",
        "terms": "pages/terms.html",
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


def journal_list(request):
    posts = JournalPost.objects.filter(is_published=True)
    return render(request, "journal/list.html", {"posts": posts})


def journal_detail(request, slug):
    from django.shortcuts import get_object_or_404
    post = get_object_or_404(JournalPost, slug=slug, is_published=True)
    more = JournalPost.objects.filter(is_published=True).exclude(pk=post.pk)[:3]
    return render(request, "journal/detail.html", {"post": post, "more": more})
