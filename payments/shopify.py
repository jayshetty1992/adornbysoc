"""
Shopify hosted-checkout handoff (Storefront API).

The Django cart drawer stays exactly as it is; at checkout time we
create a Shopify cart from the local cart lines and redirect the
customer to Shopify's hosted checkout (checkoutUrl). Payments, taxes
and order records then live in Shopify admin.

Env (see .env.example):
    SHOPIFY_STORE_DOMAIN            yourstore.myshopify.com
    SHOPIFY_STOREFRONT_ACCESS_TOKEN Storefront API access token
                                    (same custom app as the Admin token;
                                    enable Storefront API scopes:
                                    unauthenticated_write_checkouts,
                                    unauthenticated_read_product_listings)

If the env vars are missing, or any cart line has no Shopify variant
mapped (run `manage.py sync_shopify` to map them), the caller falls
back to the legacy Stripe checkout — the store never breaks.
"""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

API_VERSION = "2024-10"

CART_CREATE = """
mutation($input: CartInput!) {
  cartCreate(input: $input) {
    cart { checkoutUrl }
    userErrors { field message }
  }
}
"""


class ShopifyError(Exception):
    pass


def enabled():
    return bool(
        os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        and os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN", "").strip()
    )


def _storefront(query, variables):
    domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
    token = os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN", "").strip()
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode())
    except ShopifyError:
        raise
    except Exception as e:  # network boundary: any failure here must never 500 the checkout
        raise ShopifyError(f"Storefront API unreachable: {e}") from e
    if payload.get("errors"):
        raise ShopifyError(f"Storefront GraphQL errors: {payload['errors']}")
    return payload["data"]


def cart_checkout_url(lines, note=""):
    """
    lines: iterable of (shopify_variant_gid, qty).
    Returns the hosted checkout URL, or raises ShopifyError.
    """
    cart_input = {
        "lines": [
            {"merchandiseId": gid, "quantity": int(qty)} for gid, qty in lines
        ],
    }
    if note:
        cart_input["note"] = note[:500]

    data = _storefront(CART_CREATE, {"input": cart_input})
    result = data.get("cartCreate") or {}
    errors = result.get("userErrors") or []
    if errors:
        raise ShopifyError(f"cartCreate userErrors: {errors}")
    url = ((result.get("cart") or {}).get("checkoutUrl") or "").strip()
    if not url:
        raise ShopifyError("cartCreate returned no checkoutUrl")
    return url
