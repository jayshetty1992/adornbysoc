"""
Register the Shopify webhooks that keep the site catalog in sync.

    python manage.py register_shopify_webhooks
    python manage.py register_shopify_webhooks --url https://staging.example.com/payments/shopify/webhook/

Run ONCE after setting up the custom app (needs SHOPIFY_STORE_DOMAIN and
SHOPIFY_ADMIN_ACCESS_TOKEN in .env). Webhooks created by your own app are
signed with that app's API secret key — put it in SHOPIFY_WEBHOOK_SECRET.
"""

import json
import os
import urllib.request

from django.core.management.base import BaseCommand, CommandError

API_VERSION = "2024-10"
TOPICS = ["ORDERS_CREATE", "ORDERS_UPDATED"]
DEFAULT_URL = "https://www.adornbysoc.com/payments/shopify/webhook/"

LIST_QUERY = """
query { webhookSubscriptions(first: 25) { nodes { id topic endpoint { __typename ... on WebhookHttpEndpoint { callbackUrl } } } } }
"""

CREATE_MUTATION = """
mutation($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
  webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
    webhookSubscription { id topic }
    userErrors { field message }
  }
}
"""


class Command(BaseCommand):
    help = "Register Shopify product/inventory webhooks pointing at this site."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL, help=f"Callback URL (default {DEFAULT_URL})")

    def handle(self, *args, **opts):
        domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        token = os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "").strip()
        if not domain or not token:
            raise CommandError("SHOPIFY_STORE_DOMAIN / SHOPIFY_ADMIN_ACCESS_TOKEN missing in .env")

        url = opts["url"]
        existing = self._graphql(domain, token, LIST_QUERY, {})["webhookSubscriptions"]["nodes"]
        have = {(n["topic"], n["endpoint"].get("callbackUrl")) for n in existing}

        for topic in TOPICS:
            if (topic, url) in have:
                self.stdout.write(f"  exists: {topic} -> {url}")
                continue
            data = self._graphql(domain, token, CREATE_MUTATION, {
                "topic": topic,
                "webhookSubscription": {"callbackUrl": url, "format": "JSON"},
            })
            errs = data["webhookSubscriptionCreate"]["userErrors"]
            if errs:
                raise CommandError(f"{topic}: {errs}")
            self.stdout.write(self.style.SUCCESS(f"  created: {topic} -> {url}"))

        self.stdout.write(self.style.SUCCESS(
            "Done. Ab SHOPIFY_WEBHOOK_SECRET (custom app ki 'API secret key') .env me hona zaroori hai."
        ))

    def _graphql(self, domain, token, query, variables):
        req = urllib.request.Request(
            f"https://{domain}/admin/api/{API_VERSION}/graphql.json",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise CommandError(f"Shopify API error {e.code}: {e.read().decode()[:200]}")
        if payload.get("errors"):
            raise CommandError(f"GraphQL errors: {payload['errors']}")
        return payload["data"]
