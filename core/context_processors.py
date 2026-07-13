from catalog.models import Collection

def nav_collections(request):
    return {
        # ✅ Only select safe columns that exist
        "nav_collections": Collection.objects.only("id", "name", "slug").order_by("name")[:12]
    }

def global_brand(request):
    return {
        "BRAND_NAME": "Adorn By Soc"
    }

