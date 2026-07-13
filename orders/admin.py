from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_title", "unit_price_inr", "qty")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "subtotal_inr", "discount_inr", "total_inr", "coupon_code", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "phone", "stripe_payment_intent_id", "coupon_code")
    inlines = [OrderItemInline]
    readonly_fields = ("stripe_payment_intent_id", "stripe_client_secret", "created_at")
