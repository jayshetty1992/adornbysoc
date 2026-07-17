"""
Sync products FROM Shopify INTO the Django catalog — Storefront API only.

    python manage.py sync_shopify            # sync everything
    python manage.py sync_shopify --dry-run  # show what would change

Needs ONLY the two env vars the checkout already uses (no Admin API
token, no custom app):
    SHOPIFY_STORE_DOMAIN=xxxx.myshopify.com
    SHOPIFY_STOREFRONT_ACCESS_TOKEN=...   (Headless sales channel token)

The Storefront API returns exactly what the connected Headless channel
publishes — so "published on the Adorn Website channel" is the on/off
switch for a product appearing on the site.

Mapping:
  handle -> slug (match key)     title -> title
  description (plain) -> description
  variant price -> price_inr     compareAtPrice -> old_price_inr
  productType -> Collection (matched by name, created if missing)
  availableForSale -> in_stock   variant id -> shopify_variant_gid
  featured image -> first ProductImage (only if product has none)

Products no longer returned by Shopify (unpublished/archived/deleted)
are deactivated locally, never deleted.
"""

import json
import os
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Collection, Product, ProductImage

API_VERSION = "2024-10"

PRODUCTS_QUERY = """
query($cursor: String) {
  products(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      handle
      title
      description
      productType
      availableForSale
      featuredImage { url }
      variants(first: 1) {
        nodes { id price { amount } compareAtPrice { amount } }
      }
    }
  }
}
"""


class Command(BaseCommand):
    help = "Sync products from Shopify (Storefront API) into the local catalog."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")

    def handle(self, *args, **opts):
        domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        token = os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN", "").strip()
        if not domain or not token:
            raise CommandError(
                "Missing SHOPIFY_STORE_DOMAIN / SHOPIFY_STOREFRONT_ACCESS_TOKEN in .env "
                "(Storefront token: Sales channels > Headless > Manage > Storefront API)."
            )

        dry = opts["dry_run"]
        created = updated = imaged = 0
        seen_slugs = []
        cursor = None

        while True:
            data = self._graphql(domain, token, PRODUCTS_QUERY, {"cursor": cursor})
            block = data["products"]
            for node in block["nodes"]:
                c, u, i = self._upsert(node, dry)
                created += c
                updated += u
                imaged += i
                seen_slugs.append(node["handle"])
            if not block["pageInfo"]["hasNextPage"]:
                break
            cursor = block["pageInfo"]["endCursor"]

        # anything Shopify no longer publishes goes inactive locally
        deactivated = 0
        if not dry and seen_slugs:
            deactivated = (
                Product.objects.filter(is_active=True)
                .exclude(shopify_variant_gid="")
                .exclude(slug__in=seen_slugs)
                .update(is_active=False)
            )

        mode = "DRY RUN — nothing written. " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{mode}Shopify sync done: {created} created, {updated} updated, "
            f"{imaged} images attached, {deactivated} deactivated."
        ))

    # ---- helpers ----

    def _graphql(self, domain, token, query, variables):
        req = urllib.request.Request(
            f"https://{domain}/api/{API_VERSION}/graphql.json",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Storefront-Access-Token": token,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise CommandError(
                f"Shopify Storefront API error {e.code}: check domain/token. ({e.read().decode()[:200]})"
            )
        if payload.get("errors"):
            raise CommandError(f"Storefront GraphQL errors: {payload['errors']}")
        return payload["data"]

    def _upsert(self, node, dry):
        slug = node["handle"]
        variant = (node["variants"]["nodes"] or [None])[0]
        if not variant:
            self.stdout.write(f"  skip {slug}: no variant")
            return 0, 0, 0

        compare_at = (variant.get("compareAtPrice") or {}).get("amount")
        ptype = (node.get("productType") or "").strip() or "New Arrivals"
        fields = {
            "shopify_product_gid": node["id"],
            "shopify_variant_gid": variant["id"],
            "title": node["title"][:180],
            "description": (node.get("description") or "").strip(),
            "price_inr": variant["price"]["amount"],
            "old_price_inr": compare_at or None,
            "in_stock": bool(node.get("availableForSale")),
            "is_active": True,
        }

        if dry:
            exists = Product.objects.filter(slug=slug).exists()
            self.stdout.write(f"  {'update' if exists else 'create'} {slug} ({fields['price_inr']})")
            return (0, 1, 0) if exists else (1, 0, 0)

        collection = Collection.objects.filter(name__iexact=ptype).first()
        if collection is None:
            collection = Collection.objects.create(name=ptype, is_active=True, show_on_home=False)

        product, was_created = Product.objects.update_or_create(
            slug=slug, defaults={**fields, "collection": collection},
        )

        attached = 0
        img_url = (node.get("featuredImage") or {}).get("url")
        if img_url and not product.images.exists():
            try:
                with urllib.request.urlopen(img_url, timeout=30) as r:
                    name = os.path.basename(img_url.split("?")[0]) or f"{slug}.jpg"
                    pi = ProductImage(product=product)
                    pi.image.save(name, ContentFile(r.read()), save=True)
                    attached = 1
            except Exception as e:  # image failure shouldn't kill the sync
                self.stdout.write(f"  image failed for {slug}: {e}")

        self.stdout.write(f"  {'created' if was_created else 'updated'} {slug}")
        return (1, 0, attached) if was_created else (0, 1, attached)
