from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("collection/", views.collection_products, name="all_products"),
    path("collection/<slug:slug>/", views.collection_products, name="collection_products"),

    # old routes (optional) -> avoid breaking existing links
    path("collections/", views.collection_list, name="collection_list"),
    path("collections/<slug:slug>/", views.collection_products, name="collection_products_old"),

    # keep product_list name so existing template links don't break
    path("products/", views.collection_products, name="product_list"),

    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("try-on/<slug:slug>/", views.tryon_page, name="tryon"),
    path("sale/", views.sale_page, name="sale_page"),
    path("lookbook/", views.lookbook_page, name="lookbook"),
    path("contact/", views.contact_page, name="contact"),
    path("about/", views.about_page, name="about_page"),
    path("faq/", views.faq_page, name="faq"),
    path("wishlist/", views.wishlist_page, name="wishlist"),
    path("wishlist/state/", views.wishlist_state, name="wishlist_state"),
    path("wishlist/toggle/<slug:slug>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("review/<slug:slug>/", views.review_submit, name="review_submit"),
]
