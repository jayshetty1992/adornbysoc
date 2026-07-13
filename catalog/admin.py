from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Collection,
    Product,
    ProductImage,
    ProductFAQ,
    Lookbook,
    LookbookSection,
    LookbookGridItem,
    RingSize,
)
from .models import ContactMessage, ContactFAQ, StoreLocation
from .models import ShopTheLook, ShopTheLookItem
from .models import Tag, ProductReview, Newsletter, Coupon, SizeGuide, Wishlist


class ShopTheLookItemInline(admin.TabularInline):
    model = ShopTheLookItem
    extra = 1
    fields = ("sort_order", "product", "x", "y")
    ordering = ("sort_order", "id")


@admin.register(ShopTheLook)
class ShopTheLookAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "position", "created_at")
    list_editable = ("is_active", "position")
    ordering = ("position", "-created_at")
    inlines = [ShopTheLookItemInline]
    fields = ("title", "more_text", "more_url", "image", "is_active", "position")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "role", "alt_text", "sort_order")
    readonly_fields = ("preview",)
    ordering = ("sort_order", "id")

    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height:60px;width:60px;object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "-"  # ASCII safe


class ProductFAQInline(admin.TabularInline):
    model = ProductFAQ
    extra = 1
    fields = ("question", "answer", "is_active", "sort_order")
    ordering = ("sort_order", "id")


@admin.register(RingSize)
class RingSizeAdmin(admin.ModelAdmin):
    list_display = ("value",)
    ordering = ("value",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "show_on_home", "home_order", "card_preview")
    list_editable = ("is_active", "show_on_home", "home_order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("home_order", "name")

    fields = (
        "name", "slug",
        "card_image", "card_preview",
        "hero_image",
        "show_on_home", "home_order", "is_active",
        "meta_title", "meta_description",
    )
    readonly_fields = ("card_preview",)

    def card_preview(self, obj):
        if obj and obj.card_image:
            return format_html(
                '<img src="{}" style="height:70px;width:120px;object-fit:cover;border-radius:10px;border:1px solid #ddd;" />',
                obj.card_image.url,
            )
        return "-"  # ASCII safe


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "collection", "price_inr", "is_active", "created_at", "main_image_preview")
    list_filter = ("collection", "is_active")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)

    inlines = [ProductImageInline, ProductFAQInline]

    readonly_fields = ("created_at", "main_image_preview")
    fieldsets = (
        ("Basic Info", {
            "fields": (
                "title", "slug", "collection", "sku",
                "description",
                "price_inr", "old_price_inr",
                "in_stock", "is_active",
                "created_at", "main_image_preview",
            )
        }),
        ("Material & Stone", {
            "fields": (
                "material", "metal_purity", "weight_grams",
                "stone_type", "stone_weight_ct",
                "certificate",
            )
        }),
        ("Classification", {
            "fields": (
                "style", "color",
                "occasion", "gender",
                "ring_sizes", "tags",
            )
        }),
        ("Marketing", {
            "fields": (
                "is_featured", "is_new_arrival",
            )
        }),
        ("Content", {
            "fields": (
                "care_instructions",
            )
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": (
                "meta_title", "meta_description",
            )
        }),
    )

    def main_image_preview(self, obj):
        if not obj:
            return "-"
        img = obj.images.first()
        if img and img.image:
            return format_html(
                '<img src="{}" style="height:70px;width:70px;object-fit:cover;border-radius:10px;border:1px solid #ddd;" />',
                img.image.url,
            )
        return "-"

    def save_formset(self, request, form, formset, change):
        """
        Keeps only one Primary and one Hover image per product.
        Also supports saving FAQ inline normally.
        """
        instances = formset.save(commit=False)

        primary_seen = False
        hover_seen = False

        for obj in instances:
            # Only enforce role rules for ProductImage objects
            if isinstance(obj, ProductImage):
                if obj.role == "primary":
                    if primary_seen:
                        obj.role = "gallery"
                    primary_seen = True
                elif obj.role == "hover":
                    if hover_seen:
                        obj.role = "gallery"
                    hover_seen = True

            obj.save()

        # delete removed rows
        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "sort_order", "alt_text")
    list_filter = ("product__collection", "product")
    search_fields = ("product__title", "alt_text")
    ordering = ("product", "sort_order", "id")


@admin.register(ProductFAQ)
class ProductFAQAdmin(admin.ModelAdmin):
    list_display = ("product", "question", "is_active", "sort_order")
    list_filter = ("is_active", "product__collection", "product")
    search_fields = ("product__title", "question", "answer")
    ordering = ("product", "sort_order", "id")


@admin.register(Lookbook)
class LookbookAdmin(admin.ModelAdmin):
    list_display = ("title", "kicker", "is_active", "position", "created_at", "main_preview", "side_preview")
    list_editable = ("is_active", "position")
    ordering = ("position", "-created_at")

    fields = (
        "title",
        "kicker",
        "description",
        "main_image",
        "main_preview",
        "side_image",
        "side_preview",
        "cta_text",
        "cta_url",
        "is_active",
        "position",
    )
    readonly_fields = ("main_preview", "side_preview")

    def main_preview(self, obj):
        if obj and obj.main_image:
            return format_html(
                '<img src="{}" style="height:90px;width:140px;object-fit:cover;border-radius:10px;border:1px solid #ddd;" />',
                obj.main_image.url,
            )
        return "-"

    def side_preview(self, obj):
        if obj and obj.side_image:
            return format_html(
                '<img src="{}" style="height:90px;width:90px;object-fit:cover;border-radius:10px;border:1px solid #ddd;" />',
                obj.side_image.url,
            )
        return "-"


class LookbookGridItemInline(admin.TabularInline):
    model = LookbookGridItem
    extra = 1
    fields = ("sort_order", "preview", "image", "caption", "product")
    readonly_fields = ("preview",)
    ordering = ("sort_order", "id")

    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height:60px;width:80px;object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "-"


@admin.register(LookbookSection)
class LookbookSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "layout", "is_active", "position", "created_at")
    list_editable = ("is_active", "position")
    list_filter = ("layout", "is_active")
    ordering = ("position", "-created_at")
    search_fields = ("title",)

    fieldsets = (
        ("Basic", {"fields": ("title", "subtitle", "layout", "is_active", "position")}),
        ("Split 2 Large Images (only for layout=split2)", {
            "fields": (
                ("split_left_image", "split_left_caption", "split_left_product"),
                ("split_right_image", "split_right_caption", "split_right_product"),
            )
        }),
        ("Media + 4 Products (layout=media_products OR quote_media_products)", {
            "fields": (
                "media_side",
                "media_image",
                ("product_1", "old_price_1"),
                ("product_2", "old_price_2"),
                ("product_3", "old_price_3"),
                ("product_4", "old_price_4"),
            )
        }),
        ("Quote (layout=quote_media_products OR quote_only)", {
            "fields": ("quote_text", "quote_author", "quote_role")
        }),
    )
    inlines = [LookbookGridItemInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "reason", "created_at", "agree", "is_resolved")
    list_filter = ("reason", "is_resolved", "created_at")
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at",)


@admin.register(ContactFAQ)
class ContactFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    ordering = ("sort_order", "id")


@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active", "sort_order")
    list_filter = ("is_active", "country")
    search_fields = ("name", "address_line_1", "address_line_2", "postal_code")
    ordering = ("sort_order", "id")


# ============================================================
# JEWELRY MARKET — CUSTOMER & MARKETING ADMINS
# ============================================================

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "rating", "title", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "product__collection")
    list_editable = ("is_approved",)
    search_fields = ("name", "email", "product__title", "title", "body")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_active", "subscribed_at")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
    search_fields = ("email", "name")
    readonly_fields = ("subscribed_at",)
    ordering = ("-subscribed_at",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "min_order_amount", "is_active", "used_count", "max_uses", "valid_until")
    list_filter = ("discount_type", "is_active")
    list_editable = ("is_active",)
    search_fields = ("code",)
    readonly_fields = ("used_count", "created_at")
    ordering = ("-created_at",)
    fields = (
        "code", "discount_type", "discount_value",
        "min_order_amount", "max_discount_amount",
        "is_active", "valid_from", "valid_until",
        "max_uses", "used_count",
        "created_at",
    )


@admin.register(SizeGuide)
class SizeGuideAdmin(admin.ModelAdmin):
    list_display = ("guide_type", "title", "is_active")
    list_filter = ("is_active", "guide_type")
    list_editable = ("is_active",)
    fields = ("guide_type", "title", "content", "image", "is_active")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("product", "session_key", "added_at")
    list_filter = ("product__collection",)
    search_fields = ("product__title",)
    readonly_fields = ("added_at",)
    ordering = ("-added_at",)


from .models import JournalPost

@admin.register(JournalPost)
class JournalPostAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "published_at", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
