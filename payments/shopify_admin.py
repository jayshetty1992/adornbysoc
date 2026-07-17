"""
Django-dashboard-as-master <-> Shopify (Admin API).

THE PATTERN (what the store owner asked for):
  * Products + inventory are added/managed in the DJANGO DASHBOARD.
    Saving a product pushes it to Shopify (create or update) with price,
    compare-at, stock quantity, status and category — so Shopify checkout
    always sells exactly what the dashboard says.
  * Orders placed through the website (Shopify hosted checkout) are pulled
    back into the Django orders list: `sync_orders()` — run by the Shopify
    orders webhook and/or a cron. Local stock is decremented per line.

Needs in .env:
    SHOPIFY_STORE_DOMAIN=xxxx.myshopify.com
    SHOPIFY_ADMIN_ACCESS_TOKEN=shpat_...   (Dev Dashboard app token with
        scopes: read_products, write_products, read_inventory,
        write_inventory, read_orders)
Optional:
    SITE_URL=https://www.adornbysoc.com  (image push base; localhost images
        can't be fetched by Shopify, so image push is skipped in dev)
"""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

API_VERSION = "2024-10"

_cache = {"location": None, "publications": None}


class ShopifyAdminError(Exception):
    pass


def enabled():
    return bool(
        os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        and os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "").strip()
    )


def _admin(query, variables):
    domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
    token = os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "").strip()
    req = urllib.request.Request(
        f"https://{domain}/admin/api/{API_VERSION}/graphql.json",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except Exception as e:  # network boundary — callers degrade gracefully
        raise ShopifyAdminError(f"Admin API unreachable: {e}") from e
    if payload.get("errors"):
        raise ShopifyAdminError(f"Admin GraphQL errors: {payload['errors']}")
    return payload["data"]


def _location_id():
    if not _cache["location"]:
        data = _admin("query { locations(first: 1) { nodes { id } } }", {})
        nodes = data["locations"]["nodes"]
        if not nodes:
            raise ShopifyAdminError("No Shopify location found")
        _cache["location"] = nodes[0]["id"]
    return _cache["location"]


def _publication_ids():
    if _cache["publications"] is None:
        data = _admin("query { publications(first: 10) { nodes { id name } } }", {})
        _cache["publications"] = [
            n["id"] for n in data["publications"]["nodes"] if n["name"] != "Point of Sale"
        ]
    return _cache["publications"]


PRODUCT_SET = """
mutation($input: ProductSetInput!) {
  productSet(input: $input, synchronous: true) {
    product { id variants(first: 1) { nodes { id } } }
    userErrors { field message }
  }
}
"""

PUBLISH = """
mutation($id: ID!, $input: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $input) { userErrors { message } }
}
"""


def push_product(product):
    """
    Create/update this Django product on Shopify (price, stock, status,
    category, description). Returns True on success. Never raises for the
    caller to keep the dashboard save flow safe — errors are logged and
    surfaced via the return value.
    """
    if not enabled():
        logger.info("Shopify push skipped (admin token not configured)")
        return False
    try:
        variant = {
            "optionValues": [{"optionName": "Title", "name": "Default Title"}],
            "price": str(product.price_inr),
            "compareAtPrice": str(product.old_price_inr) if product.old_price_inr else None,
            "inventoryQuantities": [{
                "locationId": _location_id(),
                "name": "available",
                "quantity": int(product.stock_qty or 0),
            }],
        }
        inp = {
            "title": product.title,
            "handle": product.slug,
            "descriptionHtml": f"<p>{(product.description or '').strip()}</p>",
            "productType": product.collection.name if product.collection_id else "",
            "vendor": "Adorn by SOC",
            "status": "ACTIVE" if product.is_active else "DRAFT",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [variant],
        }
        if product.shopify_product_gid:
            inp["id"] = product.shopify_product_gid

        # image push: only when the URL is publicly reachable by Shopify
        site = os.getenv("SITE_URL", "https://www.adornbysoc.com").rstrip("/")
        img = product.images.first()
        if img and not product.shopify_product_gid and "localhost" not in site and "127.0.0.1" not in site:
            inp["files"] = [{"originalSource": site + img.image.url, "contentType": "IMAGE"}]

        data = _admin(PRODUCT_SET, {"input": inp})
        result = data["productSet"]
        if result["userErrors"]:
            raise ShopifyAdminError(f"productSet: {result['userErrors']}")

        node = result["product"]
        created = not product.shopify_product_gid
        variants = node["variants"]["nodes"]
        type(product).objects.filter(pk=product.pk).update(
            shopify_product_gid=node["id"],
            shopify_variant_gid=variants[0]["id"] if variants else "",
        )

        if created:
            pubs = [{"publicationId": pid} for pid in _publication_ids()]
            pub = _admin(PUBLISH, {"id": node["id"], "input": pubs})
            if pub["publishablePublish"]["userErrors"]:
                logger.warning("publish errors: %s", pub["publishablePublish"]["userErrors"])

        logger.info("Shopify push ok: %s (%s)", product.slug, "created" if created else "updated")
        return True
    except Exception:
        logger.exception("Shopify push failed for %s", product.slug)
        return False


def archive_product(product_gid):
    """Best-effort archive on Shopify when a product is deleted locally."""
    if not (enabled() and product_gid):
        return
    try:
        _admin(PRODUCT_SET, {"input": {"id": product_gid, "status": "ARCHIVED"}})
    except Exception:
        logger.exception("Shopify archive failed for %s", product_gid)


ORDERS_QUERY = """
query($cursor: String) {
  orders(first: 25, after: $cursor, reverse: true, sortKey: CREATED_AT) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id name email phone createdAt
      displayFinancialStatus
      totalPriceSet { shopMoney { amount } }
      subtotalPriceSet { shopMoney { amount } }
      totalShippingPriceSet { shopMoney { amount } }
      shippingAddress { name phone address1 address2 city province zip }
      lineItems(first: 50) {
        nodes { title quantity originalUnitPriceSet { shopMoney { amount } } variant { id } }
      }
    }
  }
}
"""


def sync_orders():
    """
    Pull recent Shopify orders into the Django orders list (idempotent by
    Shopify order id). New orders decrement local stock per line item.
    Returns (created, seen).
    """
    from orders.models import Order, OrderItem
    from catalog.models import Product

    if not enabled():
        raise ShopifyAdminError("Admin token not configured")

    data = _admin(ORDERS_QUERY, {"cursor": None})
    created = 0
    nodes = data["orders"]["nodes"]
    for node in nodes:
        if Order.objects.filter(shopify_order_id=node["id"]).exists():
            continue

        addr = node.get("shippingAddress") or {}
        status = "paid" if node["displayFinancialStatus"] in ("PAID", "PARTIALLY_REFUNDED") else "created"
        order = Order.objects.create(
            full_name=addr.get("name") or (node.get("email") or "Shopify customer"),
            phone=addr.get("phone") or node.get("phone") or "",
            email=node.get("email") or "",
            address_line1=addr.get("address1") or "",
            address_line2=addr.get("address2") or "",
            city=addr.get("city") or "",
            state=addr.get("province") or "",
            pincode=addr.get("zip") or "",
            subtotal_inr=node["subtotalPriceSet"]["shopMoney"]["amount"],
            shipping_inr=node["totalShippingPriceSet"]["shopMoney"]["amount"],
            total_inr=node["totalPriceSet"]["shopMoney"]["amount"],
            status=status,
            shopify_order_id=node["id"],
            shopify_order_name=node["name"],
            order_note=f"Imported from Shopify {node['name']}",
        )
        for li in node["lineItems"]["nodes"]:
            OrderItem.objects.create(
                order=order,
                product_title=li["title"],
                unit_price_inr=li["originalUnitPriceSet"]["shopMoney"]["amount"],
                qty=li["quantity"],
            )
            variant = li.get("variant") or {}
            if variant.get("id"):
                p = Product.objects.filter(shopify_variant_gid=variant["id"]).first()
                if p and p.stock_qty:
                    new_qty = max(0, p.stock_qty - li["quantity"])
                    Product.objects.filter(pk=p.pk).update(
                        stock_qty=new_qty, in_stock=new_qty > 0
                    )
        created += 1

    return created, len(nodes)
