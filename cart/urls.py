from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    # Existing
    path("add/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update/<int:item_id>/", views.update_qty, name="update_qty"),

    # ✅ Sidebar/AJAX
    path("sidebar/", views.cart_sidebar, name="cart_sidebar"),
    path("count/", views.cart_count_api, name="cart_count_api"),
    path("ajax/add/<slug:slug>/", views.ajax_add_to_cart, name="ajax_add_to_cart"),
    path("ajax/remove/<int:item_id>/", views.ajax_remove_item, name="ajax_remove_item"),
    path("ajax/qty/<int:item_id>/", views.ajax_change_qty, name="ajax_change_qty"),
    path("ajax/note/", views.ajax_save_note, name="ajax_save_note"),
]
