from django.db import migrations


def forwards(apps, schema_editor):
    Collection = apps.get_model("catalog", "Collection")
    JournalPost = apps.get_model("catalog", "JournalPost")

    # Rename "Necklace" -> "Necklaces & Chains" (slug stays 'necklace' so URLs keep working)
    Collection.objects.filter(slug="necklace").update(name="Necklaces & Chains")

    # New Anklets category
    Collection.objects.get_or_create(
        slug="anklets",
        defaults={"name": "Anklets", "is_active": True, "show_on_home": True, "home_order": 50},
    )

    # Seed 4 UNPUBLISHED journal drafts (titles from the SEO plan).
    # They stay invisible on the site until published from admin.
    drafts = [
        ("Does Gold Plated Jewellery Tarnish?", "does-gold-plated-jewellery-tarnish"),
        ("Can You Shower With Gold Plated Jewellery?", "can-you-shower-with-gold-plated-jewellery"),
        ("Stainless Steel vs Brass Jewellery: Which Lasts Longer?", "stainless-steel-vs-brass-jewellery"),
        ("How to Style Anti-Tarnish Jewellery for Office Wear", "style-anti-tarnish-jewellery-office-wear"),
    ]
    for title, slug in drafts:
        JournalPost.objects.get_or_create(slug=slug, defaults={"title": title, "is_published": False})


def backwards(apps, schema_editor):
    Collection = apps.get_model("catalog", "Collection")
    Collection.objects.filter(slug="necklace").update(name="Necklace")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0014_journalpost"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
