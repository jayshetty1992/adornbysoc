"""
Sync products FROM a Shopify store INTO the Django catalog.

The site keeps running on Django (cart, Stripe checkout, dashboard);
Shopify acts as a product source of truth you can sync from anytime:

    python manage.py sync_shopify            # sync all active products
    python manage.py sync_shopify --dry-run  # show what would change

Needs two env vars (add them to .env — never commit real values):
    SHOPIFY_STORE_DOMAIN=yourstore.myshopify.com
    SHOPIFY_ADMIN_ACCESS_TOKEN=shpat_xxx   (Admin API access token with
                                            read_products scope)

Mapping:
  handle -> slug (match key)   title -> title
  descriptionHtml (tags stripped) -> description
  variant price -> price_inr   compareAtPrice -> old_price_inr
  productType -> Collection (matched by name, created if missing)
  status ACTIVE -> is_active
  featured image -> first ProductImage (only if product has none)
"""

import json
import os
import re
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
      handle
      title
      descriptionHtml
      status
      productType
      featuredImage { url }
      variants(first: 1) { nodes { id price compareAtPrice } }
    }
  }
}
"""


def strip_html(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


class Command(BaseCommand):
    help = "Sync products from Shopify (Admin API) into the local catalog."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")

    def handle(self, *args, **opts):
        domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        token = os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "").strip()
        if not domain or not token:
            raise CommandError(
                "Shopify credentials missing. Add SHOPIFY_STORE_DOMAIN and "
                "SHOPIFY_ADMIN_ACCESS_TOKEN to your .env (see .env.example). "
                "Create the token in Shopify admin: Settings > Apps > Develop apps "
                "> create app > Admin API scopes: read_products."
            )

        dry = opts["dry_run"]
        created = updated = imaged = 0
        cursor = None

        while True:
            data = self._graphql(domain, token, PRODUCTS_QUERY, {"cursor": cursor})
            block = data["products"]
            for node in block["nodes"]:
                c, u, i = self._upsert(node, dry)
                created += c
                updated += u
                imaged += i
            if not block["pageInfo"]["hasNextPage"]:
                break
            cursor = block["pageInfo"]["endCursor"]

        mode = "DRY RUN — nothing written. " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{mode}Shopify sync done: {created} created, {updated} updated, {imaged} images attached."
        ))

    # ---- helpers ----

    def _graphql(self, domain, token, query, variables):
        req = urllib.request.Request(
            f"https://{domain}/admin/api/{API_VERSION}/graphql.json",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": token,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise CommandError(
                f"Shopify API error {e.code}: check the domain and token. ({e.read().decode()[:200]})"
            )
        if payload.get("errors"):
            raise CommandError(f"Shopify GraphQL errors: {payload['errors']}")
        return payload["data"]

    def _upsert(self, node, dry):
        slug = node["handle"]
        variant = (node["variants"]["nodes"] or [{}])[0]
        price = variant.get("price")
        if price is None:
            self.stdout.write(f"  skip {slug}: no variant price")
            return 0, 0, 0

        ptype = (node.get("productType") or "").strip() or "New Arrivals"
        fields = {
            "shopify_variant_gid": variant.get("id") or "",
            "title": node["title"][:180],
            "description": strip_html(node.get("descriptionHtml")),
            "price_inr": price,
            "old_price_inr": variant.get("compareAtPrice") or None,
            "is_active": node["status"] == "ACTIVE",
        }

        if dry:
            exists = Product.objects.filter(slug=slug).exists()
            self.stdout.write(f"  {'update' if exists else 'create'} {slug} ({fields['price_inr']})")
            return (0, 1, 0) if exists else (1, 0, 0)

        collection, _ = Collection.objects.get_or_create(
            name__iexact=ptype,
            defaults={"name": ptype, "is_active": True, "show_on_home": False},
        ) if not Collection.objects.filter(name__iexact=ptype).exists() else (
            Collection.objects.filter(name__iexact=ptype).first(), False,
        )

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
