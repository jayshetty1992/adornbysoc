# catalog/models.py
from django.db import models
from django.utils.text import slugify


class Collection(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    card_image = models.ImageField(upload_to="collections/cards/", blank=True, null=True)

    show_on_home = models.BooleanField(default=True)
    home_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    hero_image = models.ImageField(upload_to="collections/hero/", blank=True, null=True)
    meta_title = models.CharField(max_length=80, blank=True)
    meta_description = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RingSize(models.Model):
    value = models.DecimalField(max_digits=4, decimal_places=1, unique=True, db_index=True)

    class Meta:
        ordering = ["value"]

    def __str__(self):
        v = float(self.value)
        return str(int(v)) if v.is_integer() else str(v)


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, related_name="products")

    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    old_price_inr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # NEW: backend description
    description = models.TextField(blank=True)

    in_stock = models.BooleanField(default=True, db_index=True)
    style = models.CharField(max_length=60, blank=True, db_index=True)
    color = models.CharField(max_length=60, blank=True, db_index=True)

    ring_sizes = models.ManyToManyField(RingSize, blank=True, related_name="products")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ---- Material & Metal ----
    MATERIAL_CHOICES = [
        ("gold", "Gold"),
        ("silver", "Silver"),
        ("rose_gold", "Rose Gold"),
        ("platinum", "Platinum"),
        ("brass", "Brass"),
        ("mixed", "Mixed Metal"),
        ("other", "Other"),
    ]
    material = models.CharField(max_length=60, blank=True, db_index=True, choices=MATERIAL_CHOICES)
    metal_purity = models.CharField(max_length=40, blank=True, help_text="e.g. 18K, 22K, 925 Sterling")
    weight_grams = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)

    # ---- Stone / Gemstone ----
    STONE_CHOICES = [
        ("none", "No Stone"),
        ("diamond", "Diamond"),
        ("ruby", "Ruby"),
        ("emerald", "Emerald"),
        ("sapphire", "Sapphire"),
        ("pearl", "Pearl"),
        ("coral", "Coral"),
        ("turquoise", "Turquoise"),
        ("amethyst", "Amethyst"),
        ("cubic_zirconia", "Cubic Zirconia"),
        ("other", "Other"),
    ]
    stone_type = models.CharField(max_length=60, blank=True, choices=STONE_CHOICES)
    stone_weight_ct = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text="Stone weight in carats")

    # ---- Classification ----
    OCCASION_CHOICES = [
        ("daily", "Daily Wear"),
        ("wedding", "Wedding"),
        ("party", "Party"),
        ("festival", "Festival"),
        ("office", "Office"),
        ("gifting", "Gifting"),
    ]
    occasion = models.CharField(max_length=40, blank=True, db_index=True, choices=OCCASION_CHOICES)

    GENDER_CHOICES = [
        ("women", "Women"),
        ("men", "Men"),
        ("unisex", "Unisex"),
        ("kids", "Kids"),
    ]
    gender = models.CharField(max_length=20, blank=True, db_index=True, choices=GENDER_CHOICES, default="women")

    sku = models.CharField(max_length=80, unique=True, blank=True, null=True, help_text="Unique product code / SKU")

    # ---- Marketing flags ----
    is_featured = models.BooleanField(default=False, db_index=True)
    is_new_arrival = models.BooleanField(default=False, db_index=True)

    # ---- Content ----
    care_instructions = models.TextField(blank=True, help_text="How to clean and store this jewelry")

    # ---- SEO ----
    meta_title = models.CharField(max_length=80, blank=True)
    meta_description = models.CharField(max_length=200, blank=True)

    # ---- Certificate / Hallmark ----
    CERTIFICATE_CHOICES = [
        ("", "None"),
        ("bis", "BIS Hallmark"),
        ("igi", "IGI Certified"),
        ("gia", "GIA Certified"),
        ("igl", "IGL Certified"),
        ("other", "Other"),
    ]
    certificate = models.CharField(max_length=40, blank=True, choices=CERTIFICATE_CHOICES)

    # ---- Tags ----
    tags = models.ManyToManyField("Tag", blank=True, related_name="products")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def primary_image_obj(self):
        imgs = list(getattr(self, "images", []).all()) if hasattr(self, "images") else []
        for im in imgs:
            if getattr(im, "role", "") == "primary":
                return im
        return imgs[0] if imgs else None

    @property
    def hover_image_obj(self):
        imgs = list(getattr(self, "images", []).all()) if hasattr(self, "images") else []
        for im in imgs:
            if getattr(im, "role", "") == "hover":
                return im
        return None

    @property
    def main_image_url(self):
        im = self.primary_image_obj
        if im and im.image:
            return im.image.url
        return ""

    @property
    def is_on_sale(self):
        try:
            return self.old_price_inr is not None and self.old_price_inr > self.price_inr
        except Exception:
            return False

    @property
    def discount_percent(self):
        if not self.is_on_sale:
            return 0
        try:
            return int(round((float(self.old_price_inr) - float(self.price_inr)) / float(self.old_price_inr) * 100))
        except Exception:
            return 0

    def __str__(self):
        return self.title


class ProductFAQ(models.Model):
    """
    Per-product FAQs shown on product detail page.
    Keep content ASCII-only if your server is sensitive.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product.title} - {self.question}"


class ProductImage(models.Model):
    ROLE_CHOICES = [
        ("primary", "Primary (Product)"),
        ("hover", "Hover (Model Wearing)"),
        ("gallery", "Gallery (Extra)"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.IntegerField(default=0)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="gallery",
        db_index=True,
    )

    class Meta:
        ordering = ["sort_order", "id"]


# HERO Lookbook (your first brown section)
class Lookbook(models.Model):
    title = models.CharField(max_length=80, default="LOOKBOOK")
    kicker = models.CharField(max_length=80, default="2025 COLLECTION", blank=True)
    description = models.TextField(blank=True)

    main_image = models.ImageField(upload_to="lookbook/hero/", blank=True, null=True)
    side_image = models.ImageField(upload_to="lookbook/hero/", blank=True, null=True)

    cta_text = models.CharField(max_length=60, default="SHOP ALL JEWELRY", blank=True)
    cta_url = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created_at"]

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class LookbookSection(models.Model):
    LAYOUT_CHOICES = [
        ("grid6", "Grid (6 images)"),
        ("split2", "2 Large Images"),
        ("media_products", "Media + 4 Products"),
        ("quote_only", "Quote Only"),
    ]

    title = models.CharField(max_length=120, blank=True)
    subtitle = models.TextField(blank=True)
    layout = models.CharField(max_length=40, choices=LAYOUT_CHOICES, default="grid6")
    is_active = models.BooleanField(default=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------------
    # SPLIT2 (2 large images)
    # ---------------------------
    split_left_image = models.ImageField(upload_to="lookbook/sections/split/", blank=True, null=True)
    split_left_caption = models.CharField(max_length=140, blank=True)
    split_left_product = models.ForeignKey(
        "Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="lb_split_left"
    )

    split_right_image = models.ImageField(upload_to="lookbook/sections/split/", blank=True, null=True)
    split_right_caption = models.CharField(max_length=140, blank=True)
    split_right_product = models.ForeignKey(
        "Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="lb_split_right"
    )

    # ---------------------------
    # MEDIA + 4 PRODUCTS
    # ---------------------------
    MEDIA_SIDE = [("left", "Media Left"), ("right", "Media Right")]
    media_side = models.CharField(max_length=10, choices=MEDIA_SIDE, default="left")
    media_image = models.ImageField(upload_to="lookbook/sections/media/", blank=True, null=True)

    product_1 = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="lb_p1")
    old_price_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    product_2 = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="lb_p2")
    old_price_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    product_3 = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="lb_p3")
    old_price_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    product_4 = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="lb_p4")
    old_price_4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # ---------------------------
    # QUOTE (optional)
    # ---------------------------
    quote_text = models.TextField(blank=True)
    quote_author = models.CharField(max_length=80, blank=True)
    quote_role = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["position", "-created_at"]

    def __str__(self):
        return f"{self.title or 'Section'} [{self.layout}]"


class LookbookGridItem(models.Model):
    """
    Only for layout=grid6
    Add 6 images easily from inline
    """
    section = models.ForeignKey(LookbookSection, on_delete=models.CASCADE, related_name="grid_items")
    image = models.ImageField(upload_to="lookbook/sections/grid/")
    caption = models.CharField(max_length=140, blank=True)
    product = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"GridItem #{self.id} ({self.section_id})"
    


class ContactMessage(models.Model):
    REASON_CHOICES = [
        ("Inquiry", "Inquiry"),
        ("Order", "Order"),
        ("Shipping", "Shipping"),
        ("Returns", "Returns"),
        ("Collaboration", "Collaboration"),
        ("Other", "Other"),
    ]

    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default="Inquiry")
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    agree = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.reason} ({self.created_at.date()})"


class ContactFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.question


class StoreLocation(models.Model):
    name = models.CharField(max_length=80)  # London, Athens
    address_line_1 = models.CharField(max_length=120)
    address_line_2 = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)

    image = models.ImageField(upload_to="contact/locations/", blank=True, null=True)
    directions_url = models.URLField(blank=True)

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# --- SHOP THE LOOK (Home section) ---
class ShopTheLook(models.Model):
    title = models.CharField(max_length=80, default="SHOP THE LOOK")
    more_text = models.CharField(max_length=40, default="More looks", blank=True)
    more_url = models.CharField(max_length=255, blank=True)

    image = models.ImageField(upload_to="look/home/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created_at"]

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class ShopTheLookItem(models.Model):
    look = models.ForeignKey(ShopTheLook, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    # hotspot position on image (percentage)
    x = models.DecimalField(max_digits=5, decimal_places=2, help_text="Left % (0-100)")
    y = models.DecimalField(max_digits=5, decimal_places=2, help_text="Top % (0-100)")

    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Look#{self.look_id} -> {self.product.title}"


# ============================================================
# JEWELRY MARKET — CUSTOMER & MARKETING MODELS
# ============================================================

class ProductReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.product.title} ({self.rating}*)"


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email


class Coupon(models.Model):
    DISCOUNT_TYPE = [
        ("percent", "Percentage (%)"),
        ("flat", "Flat Amount (INR)"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE, default="percent")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Max cap for percentage coupons")

    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited uses")
    used_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        symbol = "%" if self.discount_type == "percent" else " INR"
        return f"{self.code} ({self.discount_value}{symbol})"


class SizeGuide(models.Model):
    GUIDE_TYPE = [
        ("ring", "Ring Size Guide"),
        ("bangle", "Bangle Size Guide"),
        ("bracelet", "Bracelet Size Guide"),
        ("necklace", "Necklace Length Guide"),
        ("earring", "Earring Size Guide"),
    ]

    guide_type = models.CharField(max_length=20, choices=GUIDE_TYPE, unique=True)
    title = models.CharField(max_length=120, blank=True)
    content = models.TextField(blank=True, help_text="HTML or plain text guide content")
    image = models.ImageField(upload_to="size_guides/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_guide_type_display()


class Wishlist(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session_key", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"Wish: {self.product.title}"
