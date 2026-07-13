from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    STATUS = (
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField()

    address_line1 = models.CharField(max_length=220)
    address_line2 = models.CharField(max_length=220, blank=True, default="")
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=20)

    order_note = models.TextField(blank=True, default="")

    subtotal_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True, default="")
    total_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS, default="created")

    # Stripe
    stripe_payment_intent_id = models.CharField(max_length=120, blank=True, default="")
    stripe_client_secret = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product_title = models.CharField(max_length=180)
    unit_price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)

    def line_total(self):
        return self.unit_price_inr * self.qty
