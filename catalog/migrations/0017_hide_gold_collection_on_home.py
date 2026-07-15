from django.db import migrations


def forwards(apps, schema_editor):
    Collection = apps.get_model("catalog", "Collection")
    Collection.objects.filter(slug="gold").update(show_on_home=False)


def backwards(apps, schema_editor):
    Collection = apps.get_model("catalog", "Collection")
    Collection.objects.filter(slug="gold").update(show_on_home=True)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0016_product_shopify_variant_gid")]
    operations = [migrations.RunPython(forwards, backwards)]
