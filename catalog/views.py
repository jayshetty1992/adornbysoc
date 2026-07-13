from django.db import models
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.templatetags.static import static
from django.db.models import Prefetch, Q, Count

from .models import Collection, Product, Lookbook, LookbookSection, RingSize, ProductFAQ, ProductImage
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import ContactMessage, ContactFAQ, StoreLocation


def _dec(v):
    try:
        if v is None or v == "":
            return None
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _apply_filters(qs, params, exclude=None):
    """
    Apply filters from GET params to qs.
    exclude: set of facet names to ignore for facet counting
    """
    exclude = exclude or set()

    # Availability
    if "availability" not in exclude:
        av = params.getlist("availability")
        if av:
            q = Q()
            if "in" in av:
                q |= Q(in_stock=True)
            if "out" in av:
                q |= Q(in_stock=False)
            qs = qs.filter(q)

    # Price
    if "price" not in exclude:
        min_p = _dec(params.get("min_price"))
        max_p = _dec(params.get("max_price"))
        if min_p is not None:
            qs = qs.filter(price_inr__gte=min_p)
        if max_p is not None:
            qs = qs.filter(price_inr__lte=max_p)

    # Ring size
    if "ring_size" not in exclude:
        rs = [s for s in params.getlist("ring_size") if s not in ("", None)]
        if rs:
            # ring_sizes__value in selected (OR)
            qs = qs.filter(ring_sizes__value__in=rs).distinct()

    # Style
    if "style" not in exclude:
        styles = [s.strip() for s in params.getlist("style") if s.strip()]
        if styles:
            qs = qs.filter(style__in=styles)

    # Color
    if "color" not in exclude:
        colors = [c.strip() for c in params.getlist("color") if c.strip()]
        if colors:
            qs = qs.filter(color__in=colors)

    return qs


def collection_products(request, slug=None):
    collections = Collection.objects.filter(is_active=True).order_by("home_order", "name")

    qs = (
        Product.objects.filter(is_active=True)
        .select_related("collection")
        .prefetch_related("images", "ring_sizes")
    )

    col = None
    if slug and slug not in ["all", "all-jewelry", "all-jwelery", "all-products"]:
        col = get_object_or_404(Collection, slug=slug, is_active=True)
        qs = qs.filter(collection=col)

    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(collection__slug=cat)
        if not col:
            col = Collection.objects.filter(slug=cat, is_active=True).first()

    tag = request.GET.get("tag", "").strip().lower()
    sort = request.GET.get("sort", "best").strip().lower()

    # Decide where ring size filter should appear
    # Show only on:
    # 1) ALL JEWELRY page (no collection selected)
    # 2) Rings collection page
    col_slug = (col.slug if col else "") or ""
    col_name = (col.name if col else "") or ""
    cat_slug = (cat or "").lower()

    is_ring_context = (
        (not col)
        or ("ring" in col_slug.lower())
        or ("ring" in col_name.lower())
        or ("ring" in cat_slug)
    )
    show_ring_size_filter = is_ring_context

    # Use a copy of GET params so we can ignore ring_size where not allowed
    params = request.GET.copy()
    if not show_ring_size_filter:
        params.setlist("ring_size", [])

    # Apply filters
    qs_filtered = _apply_filters(qs, params)

    # Sorting
    if sort == "new":
        qs_filtered = qs_filtered.order_by("-created_at")
    elif sort == "price_asc":
        qs_filtered = qs_filtered.order_by("price_inr", "-created_at")
    elif sort == "price_desc":
        qs_filtered = qs_filtered.order_by("-price_inr", "-created_at")
    else:
        qs_filtered = qs_filtered.order_by("-created_at")

    # Facet options
    ring_sizes = list(RingSize.objects.all()) if show_ring_size_filter else []

    style_options = list(
        qs.exclude(style="").values_list("style", flat=True).distinct().order_by("style")
    )
    color_options = list(
        qs.exclude(color="").values_list("color", flat=True).distinct().order_by("color")
    )

    # Facet counts (Shopify style)
    base_no_av = _apply_filters(qs, params, exclude={"availability"})
    base_no_price = _apply_filters(qs, params, exclude={"price"})
    base_no_rs = _apply_filters(qs, params, exclude={"ring_size"})
    base_no_style = _apply_filters(qs, params, exclude={"style"})
    base_no_color = _apply_filters(qs, params, exclude={"color"})

    availability_counts = {
        "in": base_no_av.filter(in_stock=True).count(),
        "out": base_no_av.filter(in_stock=False).count(),
    }

    max_price = qs.aggregate(m=models.Max("price_inr"))["m"] or 0
    min_price = qs.aggregate(m=models.Min("price_inr"))["m"] or 0

    # Ring size rows (only if allowed)
    ring_size_rows = []
    if show_ring_size_filter:
        tmp = {}
        rs_counts_qs = (
            base_no_rs.values("ring_sizes__value")
            .annotate(c=Count("id", distinct=True))
        )
        for x in rs_counts_qs:
            if x["ring_sizes__value"] is not None:
                tmp[str(x["ring_sizes__value"])] = x["c"]

        for rs in ring_sizes:
            key = str(rs.value)  # example: "6.0"
            ring_size_rows.append({
                "label": str(rs),   # example: "6"
                "value": key,
                "count": tmp.get(key, 0),
            })

    # Color rows (for template loop)
    color_rows = []
    if color_options:
        for c in color_options:
            color_rows.append({
                "value": c,
                "count": base_no_color.filter(color=c).count(),
            })

    # Style counts (optional)
    style_counts = {}
    if style_options:
        for s in style_options:
            style_counts[s] = base_no_style.filter(style=s).count()

    # Selected
    selected_av = params.getlist("availability")
    selected_rs = params.getlist("ring_size")
    selected_style = params.getlist("style")
    selected_color = params.getlist("color")
    selected_min = params.get("min_price", "")
    selected_max = params.get("max_price", "")

    selected_total = (
        len(selected_av) + len(selected_rs) + len(selected_style) + len(selected_color)
        + (1 if selected_min else 0) + (1 if selected_max else 0)
    )

    paginator = Paginator(qs_filtered, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    qd = request.GET.copy()
    if "page" in qd:
        qd.pop("page")
    base_qs = qd.urlencode()

    hero_title = col.name if col else "ALL JEWELRY"
    hero_desc = (
        ("Explore %s from our latest designs." % col.name)
        if col else
        "Every design in one place. Explore Earrings, Rings, Bangles and more."
    )

    hero_img_url = static("img/collections-hero.jpg")
    if col and col.card_image:
        try:
            hero_img_url = col.card_image.url
        except Exception:
            pass

    return render(request, "catalog/collection_list.html", {
        "collections": collections,
        "products": page_obj.object_list,
        "collection": col,

        "page_obj": page_obj,
        "paginator": paginator,
        "total_count": paginator.count,
        "start_index": page_obj.start_index() if paginator.count else 0,
        "end_index": page_obj.end_index() if paginator.count else 0,

        "current_sort": sort,
        "current_tag": tag,
        "current_cat": cat or (col.slug if col else ""),

        "hero_title": hero_title,
        "hero_desc": hero_desc,
        "hero_img_url": hero_img_url,

        "base_qs": base_qs,
        "selected_total": selected_total,

        "show_ring_size_filter": show_ring_size_filter,
        "ring_size_rows": ring_size_rows,

        "color_rows": color_rows,
        "style_options": style_options,

        "availability_counts": availability_counts,
        "style_counts": style_counts,

        "selected_av": selected_av,
        "selected_rs": selected_rs,
        "selected_style": selected_style,
        "selected_color": selected_color,
        "selected_min": selected_min,
        "selected_max": selected_max,

        "min_price_bound": min_price,
        "max_price_bound": max_price,
    })



def collection_list(request):
    return redirect("catalog:all_products")


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("collection").prefetch_related(
            "images",
            Prefetch("faqs", queryset=ProductFAQ.objects.filter(is_active=True).order_by("sort_order", "id")),
        ),
        slug=slug,
        is_active=True,
    )

    # product.faqs.all() is already prefetched and filtered
    faqs = list(product.faqs.all())

    return render(request, "catalog/product_detail.html", {
        "product": product,
        "faqs": faqs,
    })


def sale_page(request):
    qs = (
        Product.objects.filter(is_active=True)
        .select_related("collection")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    sort = request.GET.get("sort", "new").strip().lower()

    if sort == "price_asc":
        qs = qs.order_by("price_inr", "-created_at")
    elif sort == "price_desc":
        qs = qs.order_by("-price_inr", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "pages/sale.html", {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "total_count": paginator.count,
        "start_index": page_obj.start_index() if paginator.count else 0,
        "end_index": page_obj.end_index() if paginator.count else 0,
        "current_sort": sort,
    })


def lookbook_page(request):
    hero = Lookbook.objects.filter(is_active=True).order_by("position", "-created_at").first()
    sections = LookbookSection.objects.filter(is_active=True).prefetch_related("grid_items").order_by("position", "-created_at")
    return render(request, "catalog/lookbook.html", {"lookbook": hero, "sections": sections})


@require_http_methods(["GET", "POST"])
def contact_page(request):
    faqs = ContactFAQ.objects.filter(is_active=True).order_by("sort_order", "id")
    locations = StoreLocation.objects.filter(is_active=True).order_by("sort_order", "id")

    if request.method == "POST":
        reason = request.POST.get("reason", "Inquiry")
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message_txt = request.POST.get("message", "").strip()
        agree = True if request.POST.get("agree") == "on" else False

        if not (name and email and message_txt and agree):
            messages.error(request, "Please fill required fields and accept the agreement.")
            return render(request, "catalog/contact.html", {"faqs": faqs, "locations": locations})

        ContactMessage.objects.create(
            reason=reason,
            name=name,
            email=email,
            phone=phone,
            message=message_txt,
            agree=agree,
        )
        messages.success(request, "Thanks! Your message has been received.")
        return redirect("catalog:contact")

    return render(request, "pages/contact.html", {"faqs": faqs, "locations": locations})


def about_page(request):
    return render(request, "pages/about.html")

def faq_page(request):
    return render(request, "pages/faq.html")
