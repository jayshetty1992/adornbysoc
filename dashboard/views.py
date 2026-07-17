from decimal import Decimal
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q, Max, Min
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .decorators import staff_required
from .forms import (
    CollectionForm, ProductForm, ProductImageFormSet, ProductFAQFormSet,
    CouponForm, SizeGuideForm, TagForm,
    LookbookForm, LookbookSectionForm, LookbookGridItemFormSet,
    ShopTheLookForm, ShopTheLookItemFormSet,
    ContactFAQForm, StoreLocationForm, OrderStatusForm,
)
from catalog.models import (
    Collection, Product, ProductImage, ProductFAQ, RingSize, Tag,
    Lookbook, LookbookSection,
    ShopTheLook, ShopTheLookItem,
    SizeGuide, Coupon, Newsletter, ProductReview,
    ContactMessage, ContactFAQ, StoreLocation,
)
from orders.models import Order, OrderItem


# ============================================================
# DASHBOARD HOME
# ============================================================

@staff_required
def home(request):
    today = date.today()
    total_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    revenue = Order.objects.filter(status="paid").aggregate(t=Sum("total_inr"))["t"] or 0
    revenue_today = (
        Order.objects.filter(status="paid", created_at__date=today)
        .aggregate(t=Sum("total_inr"))["t"] or 0
    )
    orders_today = Order.objects.filter(created_at__date=today).count()
    pending_reviews = ProductReview.objects.filter(is_approved=False).count()
    low_stock = Product.objects.filter(is_active=True, in_stock=False).count()
    subscribers = Newsletter.objects.filter(is_active=True).count()
    recent_orders = Order.objects.order_by("-created_at")[:8]
    pending_messages = ContactMessage.objects.filter(is_resolved=False).count()

    order_status_counts = {
        "paid": Order.objects.filter(status="paid").count(),
        "created": Order.objects.filter(status="created").count(),
        "failed": Order.objects.filter(status="failed").count(),
        "cancelled": Order.objects.filter(status="cancelled").count(),
    }

    return render(request, "dashboard/home.html", {
        "total_products": total_products,
        "total_orders": total_orders,
        "revenue": revenue,
        "revenue_today": revenue_today,
        "orders_today": orders_today,
        "pending_reviews": pending_reviews,
        "low_stock": low_stock,
        "subscribers": subscribers,
        "recent_orders": recent_orders,
        "pending_messages": pending_messages,
        "order_status_counts": order_status_counts,
    })


# ============================================================
# PRODUCTS
# ============================================================

@staff_required
def products_list(request):
    qs = Product.objects.select_related("collection").prefetch_related("images")
    q = request.GET.get("q", "").strip()
    col = request.GET.get("col", "")
    status = request.GET.get("status", "")

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(sku__icontains=q))
    if col:
        qs = qs.filter(collection__slug=col)
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)
    elif status == "out":
        qs = qs.filter(in_stock=False)
    elif status == "featured":
        qs = qs.filter(is_featured=True)
    elif status == "new":
        qs = qs.filter(is_new_arrival=True)

    qs = qs.order_by("-created_at")
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    collections = Collection.objects.filter(is_active=True).order_by("name")

    return render(request, "dashboard/products_list.html", {
        "page_obj": page_obj,
        "collections": collections,
        "current_q": q,
        "current_col": col,
        "current_status": status,
        "total_count": paginator.count,
    })


@staff_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            saved = form.save()
            img_fs = ProductImageFormSet(request.POST, request.FILES, instance=saved)
            faq_fs = ProductFAQFormSet(request.POST, instance=saved)
            if img_fs.is_valid() and faq_fs.is_valid():
                img_fs.save()
                faq_fs.save()
                from payments import shopify_admin
                if shopify_admin.enabled():
                    if shopify_admin.push_product(saved):
                        messages.success(request, "Product saved and pushed to Shopify.")
                    else:
                        messages.warning(request, "Product saved, but the Shopify push failed - check logs and save again.")
                else:
                    messages.success(request, "Product saved successfully.")
                return redirect("dashboard:products_list")
            else:
                img_fs_err = img_fs
                faq_fs_err = faq_fs
        else:
            img_fs_err = ProductImageFormSet(request.POST, request.FILES, instance=product)
            faq_fs_err = ProductFAQFormSet(request.POST, instance=product)
        image_formset = img_fs_err
        faq_formset = faq_fs_err
    else:
        form = ProductForm(instance=product)
        image_formset = ProductImageFormSet(instance=product)
        faq_formset = ProductFAQFormSet(instance=product)

    return render(request, "dashboard/products_form.html", {
        "form": form,
        "image_formset": image_formset,
        "faq_formset": faq_formset,
        "product": product,
        "title": "Edit Product" if product else "Add Product",
        "collections": Collection.objects.filter(is_active=True),
    })


@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.title
    gid = product.shopify_product_gid
    product.delete()
    from payments import shopify_admin
    shopify_admin.archive_product(gid)
    messages.success(request, f'Product "{name}" deleted.')
    return redirect("dashboard:products_list")


@staff_required
@require_POST
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    from payments import shopify_admin
    if shopify_admin.enabled():
        shopify_admin.push_product(product)
    return redirect("dashboard:products_list")


# ============================================================
# COLLECTIONS
# ============================================================

@staff_required
def collections_list(request):
    cols = Collection.objects.annotate(product_count=Count("products")).order_by("home_order", "name")
    return render(request, "dashboard/collections_list.html", {"collections": cols})


@staff_required
def collection_form(request, pk=None):
    collection = get_object_or_404(Collection, pk=pk) if pk else None

    if request.method == "POST":
        form = CollectionForm(request.POST, request.FILES, instance=collection)
        if form.is_valid():
            form.save()
            messages.success(request, "Collection saved.")
            return redirect("dashboard:collections_list")
    else:
        form = CollectionForm(instance=collection)

    return render(request, "dashboard/collections_form.html", {
        "form": form,
        "collection": collection,
        "title": "Edit Collection" if collection else "Add Collection",
    })


@staff_required
@require_POST
def collection_delete(request, pk):
    col = get_object_or_404(Collection, pk=pk)
    try:
        name = col.name
        col.delete()
        messages.success(request, f'Collection "{name}" deleted.')
    except Exception:
        messages.error(request, "Cannot delete — products are linked to this collection.")
    return redirect("dashboard:collections_list")


# ============================================================
# ORDERS
# ============================================================

@staff_required
def orders_list(request):
    qs = Order.objects.order_by("-created_at")
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()

    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(full_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
        )

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    stats = {
        "all": Order.objects.count(),
        "paid": Order.objects.filter(status="paid").count(),
        "created": Order.objects.filter(status="created").count(),
        "failed": Order.objects.filter(status="failed").count(),
        "cancelled": Order.objects.filter(status="cancelled").count(),
    }
    return render(request, "dashboard/orders_list.html", {
        "page_obj": page_obj,
        "current_status": status,
        "current_q": q,
        "stats": stats,
    })


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)

    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "Order status updated.")
            return redirect("dashboard:order_detail", pk=pk)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, "dashboard/orders_detail.html", {
        "order": order,
        "status_form": form,
    })


# ============================================================
# REVIEWS
# ============================================================

@staff_required
def reviews_list(request):
    qs = ProductReview.objects.select_related("product").order_by("-created_at")
    status = request.GET.get("status", "")
    if status == "pending":
        qs = qs.filter(is_approved=False)
    elif status == "approved":
        qs = qs.filter(is_approved=True)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/reviews_list.html", {
        "page_obj": page_obj,
        "current_status": status,
        "pending_count": ProductReview.objects.filter(is_approved=False).count(),
    })


@staff_required
@require_POST
def review_toggle(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)
    review.is_approved = not review.is_approved
    review.save(update_fields=["is_approved"])
    return redirect(request.META.get("HTTP_REFERER", "dashboard:reviews_list"))


@staff_required
@require_POST
def review_delete(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)
    review.delete()
    messages.success(request, "Review deleted.")
    return redirect("dashboard:reviews_list")


# ============================================================
# COUPONS
# ============================================================

@staff_required
def coupons_list(request):
    coupons = Coupon.objects.order_by("-created_at")
    return render(request, "dashboard/coupons_list.html", {"coupons": coupons})


@staff_required
def coupon_form(request, pk=None):
    coupon = get_object_or_404(Coupon, pk=pk) if pk else None

    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon saved.")
            return redirect("dashboard:coupons_list")
    else:
        form = CouponForm(instance=coupon)

    return render(request, "dashboard/coupons_form.html", {
        "form": form,
        "coupon": coupon,
        "title": "Edit Coupon" if coupon else "Add Coupon",
    })


@staff_required
@require_POST
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    code = coupon.code
    coupon.delete()
    messages.success(request, f'Coupon "{code}" deleted.')
    return redirect("dashboard:coupons_list")


@staff_required
@require_POST
def coupon_toggle(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save(update_fields=["is_active"])
    return redirect("dashboard:coupons_list")


# ============================================================
# NEWSLETTER
# ============================================================

@staff_required
def newsletter_list(request):
    qs = Newsletter.objects.order_by("-subscribed_at")
    status = request.GET.get("status", "")
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 30)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/newsletter_list.html", {
        "page_obj": page_obj,
        "current_status": status,
        "total": Newsletter.objects.count(),
        "active_count": Newsletter.objects.filter(is_active=True).count(),
    })


@staff_required
@require_POST
def newsletter_toggle(request, pk):
    sub = get_object_or_404(Newsletter, pk=pk)
    sub.is_active = not sub.is_active
    sub.save(update_fields=["is_active"])
    return redirect("dashboard:newsletter_list")


@staff_required
@require_POST
def newsletter_delete(request, pk):
    sub = get_object_or_404(Newsletter, pk=pk)
    sub.delete()
    return redirect("dashboard:newsletter_list")


# ============================================================
# TAGS
# ============================================================

@staff_required
def tags_list(request):
    tags = Tag.objects.annotate(product_count=Count("products")).order_by("name")
    form = TagForm()

    if request.method == "POST":
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tag added.")
            return redirect("dashboard:tags_list")

    return render(request, "dashboard/tags_list.html", {"tags": tags, "form": form})


@staff_required
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    form = TagForm(request.POST or None, instance=tag)
    if form.is_valid():
        form.save()
        messages.success(request, "Tag updated.")
        return redirect("dashboard:tags_list")
    return render(request, "dashboard/tags_list.html", {
        "tags": Tag.objects.annotate(product_count=Count("products")).order_by("name"),
        "form": form,
        "editing_tag": tag,
    })


@staff_required
@require_POST
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    tag.delete()
    messages.success(request, "Tag deleted.")
    return redirect("dashboard:tags_list")


# ============================================================
# RING SIZES
# ============================================================

@staff_required
def ring_sizes_list(request):
    sizes = RingSize.objects.order_by("value")

    if request.method == "POST":
        value = request.POST.get("value", "").strip()
        if value:
            try:
                RingSize.objects.get_or_create(value=Decimal(value))
                messages.success(request, f"Ring size {value} added.")
            except Exception:
                messages.error(request, "Invalid value. Please enter a number like 6 or 6.5")
        return redirect("dashboard:ring_sizes_list")

    return render(request, "dashboard/ring_sizes_list.html", {"sizes": sizes})


@staff_required
@require_POST
def ring_size_delete(request, pk):
    size = get_object_or_404(RingSize, pk=pk)
    val = size.value
    size.delete()
    messages.success(request, f"Ring size {val} deleted.")
    return redirect("dashboard:ring_sizes_list")


# ============================================================
# SIZE GUIDES
# ============================================================

@staff_required
def size_guides_list(request):
    guides = SizeGuide.objects.all()
    return render(request, "dashboard/size_guides_list.html", {"guides": guides})


@staff_required
def size_guide_form(request, pk=None):
    guide = get_object_or_404(SizeGuide, pk=pk) if pk else None

    if request.method == "POST":
        form = SizeGuideForm(request.POST, request.FILES, instance=guide)
        if form.is_valid():
            form.save()
            messages.success(request, "Size guide saved.")
            return redirect("dashboard:size_guides_list")
    else:
        form = SizeGuideForm(instance=guide)

    return render(request, "dashboard/size_guide_form.html", {
        "form": form,
        "guide": guide,
        "title": "Edit Size Guide" if guide else "Add Size Guide",
    })


@staff_required
@require_POST
def size_guide_delete(request, pk):
    guide = get_object_or_404(SizeGuide, pk=pk)
    guide.delete()
    messages.success(request, "Size guide deleted.")
    return redirect("dashboard:size_guides_list")


# ============================================================
# CONTACT MESSAGES
# ============================================================

@staff_required
def contact_messages_list(request):
    qs = ContactMessage.objects.order_by("-created_at")
    status = request.GET.get("status", "")
    if status == "pending":
        qs = qs.filter(is_resolved=False)
    elif status == "resolved":
        qs = qs.filter(is_resolved=True)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/contact_list.html", {
        "page_obj": page_obj,
        "current_status": status,
        "pending_count": ContactMessage.objects.filter(is_resolved=False).count(),
    })


@staff_required
@require_POST
def contact_resolve(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_resolved = not msg.is_resolved
    msg.save(update_fields=["is_resolved"])
    return redirect("dashboard:contact_messages_list")


@staff_required
@require_POST
def contact_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.delete()
    return redirect("dashboard:contact_messages_list")


# ============================================================
# CONTACT FAQs
# ============================================================

@staff_required
def contact_faqs_list(request):
    faqs = ContactFAQ.objects.order_by("sort_order", "id")
    form = ContactFAQForm()

    if request.method == "POST":
        form = ContactFAQForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "FAQ added.")
            return redirect("dashboard:contact_faqs_list")

    return render(request, "dashboard/contact_faqs_list.html", {"faqs": faqs, "form": form})


@staff_required
def contact_faq_edit(request, pk):
    faq = get_object_or_404(ContactFAQ, pk=pk)
    form = ContactFAQForm(request.POST or None, instance=faq)
    if form.is_valid():
        form.save()
        messages.success(request, "FAQ updated.")
        return redirect("dashboard:contact_faqs_list")
    return render(request, "dashboard/contact_faqs_list.html", {
        "faqs": ContactFAQ.objects.order_by("sort_order", "id"),
        "form": form,
        "editing_faq": faq,
    })


@staff_required
@require_POST
def contact_faq_delete(request, pk):
    faq = get_object_or_404(ContactFAQ, pk=pk)
    faq.delete()
    return redirect("dashboard:contact_faqs_list")


# ============================================================
# STORE LOCATIONS
# ============================================================

@staff_required
def store_locations_list(request):
    locations = StoreLocation.objects.order_by("sort_order")
    return render(request, "dashboard/store_locations_list.html", {"locations": locations})


@staff_required
def store_location_form(request, pk=None):
    location = get_object_or_404(StoreLocation, pk=pk) if pk else None

    if request.method == "POST":
        form = StoreLocationForm(request.POST, request.FILES, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, "Location saved.")
            return redirect("dashboard:store_locations_list")
    else:
        form = StoreLocationForm(instance=location)

    return render(request, "dashboard/store_location_form.html", {
        "form": form,
        "location": location,
        "title": "Edit Location" if location else "Add Location",
    })


@staff_required
@require_POST
def store_location_delete(request, pk):
    loc = get_object_or_404(StoreLocation, pk=pk)
    loc.delete()
    messages.success(request, "Location deleted.")
    return redirect("dashboard:store_locations_list")


# ============================================================
# LOOKBOOK HERO
# ============================================================

@staff_required
def lookbook_list(request):
    lookbooks = Lookbook.objects.order_by("position", "-created_at")
    return render(request, "dashboard/lookbook_list.html", {"lookbooks": lookbooks})


@staff_required
def lookbook_form(request, pk=None):
    lookbook = get_object_or_404(Lookbook, pk=pk) if pk else None

    if request.method == "POST":
        form = LookbookForm(request.POST, request.FILES, instance=lookbook)
        if form.is_valid():
            form.save()
            messages.success(request, "Lookbook entry saved.")
            return redirect("dashboard:lookbook_list")
    else:
        form = LookbookForm(instance=lookbook)

    return render(request, "dashboard/lookbook_form.html", {
        "form": form,
        "lookbook": lookbook,
        "title": "Edit Lookbook" if lookbook else "Add Lookbook",
    })


@staff_required
@require_POST
def lookbook_delete(request, pk):
    lb = get_object_or_404(Lookbook, pk=pk)
    lb.delete()
    messages.success(request, "Lookbook entry deleted.")
    return redirect("dashboard:lookbook_list")


# ============================================================
# LOOKBOOK SECTIONS
# ============================================================

@staff_required
def lookbook_sections_list(request):
    sections = LookbookSection.objects.prefetch_related("grid_items").order_by("position", "-created_at")
    return render(request, "dashboard/lookbook_sections_list.html", {"sections": sections})


@staff_required
def lookbook_section_form(request, pk=None):
    section = get_object_or_404(LookbookSection, pk=pk) if pk else None

    if request.method == "POST":
        form = LookbookSectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            saved = form.save()
            grid_fs = LookbookGridItemFormSet(request.POST, request.FILES, instance=saved)
            if grid_fs.is_valid():
                grid_fs.save()
            messages.success(request, "Lookbook section saved.")
            return redirect("dashboard:lookbook_sections_list")
        grid_formset = LookbookGridItemFormSet(request.POST, request.FILES, instance=section)
    else:
        form = LookbookSectionForm(instance=section)
        grid_formset = LookbookGridItemFormSet(instance=section)

    return render(request, "dashboard/lookbook_section_form.html", {
        "form": form,
        "grid_formset": grid_formset,
        "section": section,
        "title": "Edit Section" if section else "Add Lookbook Section",
    })


@staff_required
@require_POST
def lookbook_section_delete(request, pk):
    section = get_object_or_404(LookbookSection, pk=pk)
    section.delete()
    messages.success(request, "Section deleted.")
    return redirect("dashboard:lookbook_sections_list")


# ============================================================
# SHOP THE LOOK
# ============================================================

@staff_required
def shop_the_look_list(request):
    looks = ShopTheLook.objects.prefetch_related("items").order_by("position", "-created_at")
    return render(request, "dashboard/shop_the_look_list.html", {"looks": looks})


@staff_required
def shop_the_look_form(request, pk=None):
    look = get_object_or_404(ShopTheLook, pk=pk) if pk else None

    if request.method == "POST":
        form = ShopTheLookForm(request.POST, request.FILES, instance=look)
        if form.is_valid():
            saved = form.save()
            item_fs = ShopTheLookItemFormSet(request.POST, instance=saved)
            if item_fs.is_valid():
                item_fs.save()
            messages.success(request, "Shop The Look saved.")
            return redirect("dashboard:shop_the_look_list")
        item_formset = ShopTheLookItemFormSet(request.POST, instance=look)
    else:
        form = ShopTheLookForm(instance=look)
        item_formset = ShopTheLookItemFormSet(instance=look)

    return render(request, "dashboard/shop_the_look_form.html", {
        "form": form,
        "item_formset": item_formset,
        "look": look,
        "title": "Edit Look" if look else "Add Shop The Look",
    })


@staff_required
@require_POST
def shop_the_look_delete(request, pk):
    look = get_object_or_404(ShopTheLook, pk=pk)
    look.delete()
    messages.success(request, "Look deleted.")
    return redirect("dashboard:shop_the_look_list")
