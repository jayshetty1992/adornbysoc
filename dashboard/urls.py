from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Products
    path("products/", views.products_list, name="products_list"),
    path("products/add/", views.product_form, name="product_add"),
    path("products/<int:pk>/edit/", views.product_form, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:pk>/toggle/", views.product_toggle_active, name="product_toggle"),

    # Collections
    path("collections/", views.collections_list, name="collections_list"),
    path("collections/add/", views.collection_form, name="collection_add"),
    path("collections/<int:pk>/edit/", views.collection_form, name="collection_edit"),
    path("collections/<int:pk>/delete/", views.collection_delete, name="collection_delete"),

    # Orders
    path("orders/", views.orders_list, name="orders_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),

    # Reviews
    path("reviews/", views.reviews_list, name="reviews_list"),
    path("reviews/<int:pk>/toggle/", views.review_toggle, name="review_toggle"),
    path("reviews/<int:pk>/delete/", views.review_delete, name="review_delete"),

    # Coupons
    path("coupons/", views.coupons_list, name="coupons_list"),
    path("coupons/add/", views.coupon_form, name="coupon_add"),
    path("coupons/<int:pk>/edit/", views.coupon_form, name="coupon_edit"),
    path("coupons/<int:pk>/delete/", views.coupon_delete, name="coupon_delete"),
    path("coupons/<int:pk>/toggle/", views.coupon_toggle, name="coupon_toggle"),

    # Newsletter
    path("newsletter/", views.newsletter_list, name="newsletter_list"),
    path("newsletter/<int:pk>/toggle/", views.newsletter_toggle, name="newsletter_toggle"),
    path("newsletter/<int:pk>/delete/", views.newsletter_delete, name="newsletter_delete"),

    # Tags
    path("tags/", views.tags_list, name="tags_list"),
    path("tags/<int:pk>/edit/", views.tag_edit, name="tag_edit"),
    path("tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),

    # Ring Sizes
    path("ring-sizes/", views.ring_sizes_list, name="ring_sizes_list"),
    path("ring-sizes/<int:pk>/delete/", views.ring_size_delete, name="ring_size_delete"),

    # Size Guides
    path("size-guides/", views.size_guides_list, name="size_guides_list"),
    path("size-guides/add/", views.size_guide_form, name="size_guide_add"),
    path("size-guides/<int:pk>/edit/", views.size_guide_form, name="size_guide_edit"),
    path("size-guides/<int:pk>/delete/", views.size_guide_delete, name="size_guide_delete"),

    # Contact Messages
    path("contact-messages/", views.contact_messages_list, name="contact_messages_list"),
    path("contact-messages/<int:pk>/resolve/", views.contact_resolve, name="contact_resolve"),
    path("contact-messages/<int:pk>/delete/", views.contact_delete, name="contact_delete"),

    # Contact FAQs
    path("contact-faqs/", views.contact_faqs_list, name="contact_faqs_list"),
    path("contact-faqs/<int:pk>/edit/", views.contact_faq_edit, name="contact_faq_edit"),
    path("contact-faqs/<int:pk>/delete/", views.contact_faq_delete, name="contact_faq_delete"),

    # Store Locations
    path("store-locations/", views.store_locations_list, name="store_locations_list"),
    path("store-locations/add/", views.store_location_form, name="store_location_add"),
    path("store-locations/<int:pk>/edit/", views.store_location_form, name="store_location_edit"),
    path("store-locations/<int:pk>/delete/", views.store_location_delete, name="store_location_delete"),

    # Lookbook
    path("lookbook/", views.lookbook_list, name="lookbook_list"),
    path("lookbook/add/", views.lookbook_form, name="lookbook_add"),
    path("lookbook/<int:pk>/edit/", views.lookbook_form, name="lookbook_edit"),
    path("lookbook/<int:pk>/delete/", views.lookbook_delete, name="lookbook_delete"),

    # Lookbook Sections
    path("lookbook-sections/", views.lookbook_sections_list, name="lookbook_sections_list"),
    path("lookbook-sections/add/", views.lookbook_section_form, name="lookbook_section_add"),
    path("lookbook-sections/<int:pk>/edit/", views.lookbook_section_form, name="lookbook_section_edit"),
    path("lookbook-sections/<int:pk>/delete/", views.lookbook_section_delete, name="lookbook_section_delete"),

    # Shop The Look
    path("shop-the-look/", views.shop_the_look_list, name="shop_the_look_list"),
    path("shop-the-look/add/", views.shop_the_look_form, name="shop_the_look_add"),
    path("shop-the-look/<int:pk>/edit/", views.shop_the_look_form, name="shop_the_look_edit"),
    path("shop-the-look/<int:pk>/delete/", views.shop_the_look_delete, name="shop_the_look_delete"),
]
