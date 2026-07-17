"""
Pull recent Shopify orders into the Django orders list (idempotent).
Run by cron as a webhook backup:  */5 * * * *  python manage.py sync_shopify_orders
"""
from django.core.management.base import BaseCommand, CommandError

from payments import shopify_admin


class Command(BaseCommand):
    help = "Import recent Shopify orders into the local orders list."

    def handle(self, *args, **opts):
        try:
            created, seen = shopify_admin.sync_orders()
        except shopify_admin.ShopifyAdminError as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(f"Orders sync: {created} new, {seen} checked."))
