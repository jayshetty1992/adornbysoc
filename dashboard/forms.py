from django import forms
from django.forms import inlineformset_factory

from catalog.models import (
    Collection, Product, ProductImage, ProductFAQ,
    RingSize, Tag,
    Lookbook, LookbookSection, LookbookGridItem,
    ShopTheLook, ShopTheLookItem,
    SizeGuide, Coupon,
    ContactFAQ, StoreLocation,
)
from orders.models import Order


def _w(extra="", tag="input"):
    base = "form-control " + extra
    return {"class": base.strip()}


def _sel(extra=""):
    return {"class": ("form-select " + extra).strip()}


def _check():
    return {"class": "form-check-input"}


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = [
            "name", "slug", "card_image", "hero_image",
            "show_on_home", "home_order", "is_active",
            "meta_title", "meta_description",
        ]
        widgets = {
            "name": forms.TextInput(_w()),
            "slug": forms.TextInput(_w()),
            "home_order": forms.NumberInput(_w()),
            "meta_title": forms.TextInput(_w()),
            "meta_description": forms.Textarea({**_w(), "rows": 2}),
            "show_on_home": forms.CheckboxInput(_check()),
            "is_active": forms.CheckboxInput(_check()),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "title", "slug", "collection", "description",
            "price_inr", "old_price_inr", "stock_qty", "in_stock", "is_active",
            "material", "metal_purity", "weight_grams",
            "stone_type", "stone_weight_ct",
            "occasion", "gender", "sku", "certificate",
            "style", "color", "ring_sizes", "tags",
            "is_featured", "is_new_arrival",
            "tryon_enabled", "tryon_type", "tryon_image",
            "care_instructions", "meta_title", "meta_description",
        ]
        widgets = {
            "title": forms.TextInput(_w()),
            "slug": forms.TextInput(_w()),
            "collection": forms.Select(_sel()),
            "description": forms.Textarea({**_w(), "rows": 4}),
            "price_inr": forms.NumberInput(_w()),
            "old_price_inr": forms.NumberInput(_w()),
            "stock_qty": forms.NumberInput(_w()),
            "material": forms.Select(_sel()),
            "metal_purity": forms.TextInput(_w()),
            "weight_grams": forms.NumberInput(_w()),
            "stone_type": forms.Select(_sel()),
            "stone_weight_ct": forms.NumberInput(_w()),
            "occasion": forms.Select(_sel()),
            "gender": forms.Select(_sel()),
            "sku": forms.TextInput(_w()),
            "certificate": forms.Select(_sel()),
            "style": forms.TextInput(_w()),
            "color": forms.TextInput(_w()),
            "ring_sizes": forms.CheckboxSelectMultiple(),
            "tags": forms.CheckboxSelectMultiple(),
            "care_instructions": forms.Textarea({**_w(), "rows": 3}),
            "meta_title": forms.TextInput(_w()),
            "meta_description": forms.Textarea({**_w(), "rows": 2}),
            "in_stock": forms.CheckboxInput(_check()),
            "is_active": forms.CheckboxInput(_check()),
            "is_featured": forms.CheckboxInput(_check()),
            "is_new_arrival": forms.CheckboxInput(_check()),
            "tryon_enabled": forms.CheckboxInput(_check()),
            "tryon_type": forms.Select(_sel()),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "role", "alt_text", "sort_order"]
        widgets = {
            "role": forms.Select(_sel("form-select-sm")),
            "alt_text": forms.TextInput({**_w("form-control-sm")}),
            "sort_order": forms.NumberInput({**_w("form-control-sm"), "style": "width:70px"}),
        }


class ProductFAQForm(forms.ModelForm):
    class Meta:
        model = ProductFAQ
        fields = ["question", "answer", "is_active", "sort_order"]
        widgets = {
            "question": forms.TextInput(_w()),
            "answer": forms.Textarea({**_w(), "rows": 2}),
            "sort_order": forms.NumberInput({**_w(), "style": "width:70px"}),
            "is_active": forms.CheckboxInput(_check()),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "code", "discount_type", "discount_value",
            "min_order_amount", "max_discount_amount",
            "is_active", "valid_from", "valid_until", "max_uses",
        ]
        widgets = {
            "code": forms.TextInput(_w()),
            "discount_type": forms.Select(_sel()),
            "discount_value": forms.NumberInput(_w()),
            "min_order_amount": forms.NumberInput(_w()),
            "max_discount_amount": forms.NumberInput(_w()),
            "valid_from": forms.DateTimeInput(
                {**_w(), "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "valid_until": forms.DateTimeInput(
                {**_w(), "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "max_uses": forms.NumberInput(_w()),
            "is_active": forms.CheckboxInput(_check()),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        if inst and inst.valid_from:
            self.fields["valid_from"].initial = inst.valid_from.strftime("%Y-%m-%dT%H:%M")
        if inst and inst.valid_until:
            self.fields["valid_until"].initial = inst.valid_until.strftime("%Y-%m-%dT%H:%M")


class SizeGuideForm(forms.ModelForm):
    class Meta:
        model = SizeGuide
        fields = ["guide_type", "title", "content", "image", "is_active"]
        widgets = {
            "guide_type": forms.Select(_sel()),
            "title": forms.TextInput(_w()),
            "content": forms.Textarea({**_w(), "rows": 10}),
            "is_active": forms.CheckboxInput(_check()),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "slug"]
        widgets = {
            "name": forms.TextInput(_w()),
            "slug": forms.TextInput(_w()),
        }


class LookbookForm(forms.ModelForm):
    class Meta:
        model = Lookbook
        fields = [
            "title", "kicker", "description",
            "main_image", "side_image",
            "cta_text", "cta_url",
            "is_active", "position",
        ]
        widgets = {
            "title": forms.TextInput(_w()),
            "kicker": forms.TextInput(_w()),
            "description": forms.Textarea({**_w(), "rows": 3}),
            "cta_text": forms.TextInput(_w()),
            "cta_url": forms.TextInput(_w()),
            "position": forms.NumberInput(_w()),
            "is_active": forms.CheckboxInput(_check()),
        }


class LookbookSectionForm(forms.ModelForm):
    class Meta:
        model = LookbookSection
        fields = [
            "title", "subtitle", "layout", "is_active", "position",
            "split_left_image", "split_left_caption", "split_left_product",
            "split_right_image", "split_right_caption", "split_right_product",
            "media_side", "media_image",
            "product_1", "old_price_1", "product_2", "old_price_2",
            "product_3", "old_price_3", "product_4", "old_price_4",
            "quote_text", "quote_author", "quote_role",
        ]
        widgets = {
            "title": forms.TextInput(_w()),
            "subtitle": forms.Textarea({**_w(), "rows": 2}),
            "layout": forms.Select(_sel()),
            "position": forms.NumberInput(_w()),
            "is_active": forms.CheckboxInput(_check()),
            "split_left_caption": forms.TextInput(_w()),
            "split_left_product": forms.Select(_sel()),
            "split_right_caption": forms.TextInput(_w()),
            "split_right_product": forms.Select(_sel()),
            "media_side": forms.Select(_sel()),
            "product_1": forms.Select(_sel()),
            "old_price_1": forms.NumberInput(_w()),
            "product_2": forms.Select(_sel()),
            "old_price_2": forms.NumberInput(_w()),
            "product_3": forms.Select(_sel()),
            "old_price_3": forms.NumberInput(_w()),
            "product_4": forms.Select(_sel()),
            "old_price_4": forms.NumberInput(_w()),
            "quote_text": forms.Textarea({**_w(), "rows": 3}),
            "quote_author": forms.TextInput(_w()),
            "quote_role": forms.TextInput(_w()),
        }


class LookbookGridItemForm(forms.ModelForm):
    class Meta:
        model = LookbookGridItem
        fields = ["image", "caption", "product", "sort_order"]
        widgets = {
            "caption": forms.TextInput({**_w("form-control-sm")}),
            "product": forms.Select(_sel("form-select-sm")),
            "sort_order": forms.NumberInput({**_w("form-control-sm"), "style": "width:70px"}),
        }


class ShopTheLookForm(forms.ModelForm):
    class Meta:
        model = ShopTheLook
        fields = ["title", "more_text", "more_url", "image", "is_active", "position"]
        widgets = {
            "title": forms.TextInput(_w()),
            "more_text": forms.TextInput(_w()),
            "more_url": forms.TextInput(_w()),
            "position": forms.NumberInput(_w()),
            "is_active": forms.CheckboxInput(_check()),
        }


class ShopTheLookItemForm(forms.ModelForm):
    class Meta:
        model = ShopTheLookItem
        fields = ["product", "x", "y", "sort_order"]
        widgets = {
            "product": forms.Select(_sel("form-select-sm")),
            "x": forms.NumberInput({**_w("form-control-sm")}),
            "y": forms.NumberInput({**_w("form-control-sm")}),
            "sort_order": forms.NumberInput({**_w("form-control-sm"), "style": "width:70px"}),
        }


class ContactFAQForm(forms.ModelForm):
    class Meta:
        model = ContactFAQ
        fields = ["question", "answer", "is_active", "sort_order"]
        widgets = {
            "question": forms.TextInput(_w()),
            "answer": forms.Textarea({**_w(), "rows": 3}),
            "sort_order": forms.NumberInput(_w()),
            "is_active": forms.CheckboxInput(_check()),
        }


class StoreLocationForm(forms.ModelForm):
    class Meta:
        model = StoreLocation
        fields = [
            "name", "address_line_1", "address_line_2", "postal_code",
            "country", "image", "directions_url", "sort_order", "is_active",
        ]
        widgets = {
            "name": forms.TextInput(_w()),
            "address_line_1": forms.TextInput(_w()),
            "address_line_2": forms.TextInput(_w()),
            "postal_code": forms.TextInput(_w()),
            "country": forms.TextInput(_w()),
            "directions_url": forms.URLInput(_w()),
            "sort_order": forms.NumberInput(_w()),
            "is_active": forms.CheckboxInput(_check()),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]
        widgets = {"status": forms.Select(_sel())}


# ---- Inline Formsets ----
ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=3, can_delete=True,
)

ProductFAQFormSet = inlineformset_factory(
    Product, ProductFAQ, form=ProductFAQForm, extra=2, can_delete=True,
)

LookbookGridItemFormSet = inlineformset_factory(
    LookbookSection, LookbookGridItem, form=LookbookGridItemForm, extra=3, can_delete=True,
)

ShopTheLookItemFormSet = inlineformset_factory(
    ShopTheLook, ShopTheLookItem, form=ShopTheLookItemForm, extra=3, can_delete=True,
)
