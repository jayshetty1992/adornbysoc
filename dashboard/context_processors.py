from catalog.models import ProductReview, ContactMessage


def dashboard_globals(request):
    if (
        request.user.is_authenticated
        and request.user.is_staff
        and request.path.startswith("/dashboard/")
    ):
        return {
            "pending_reviews_count": ProductReview.objects.filter(is_approved=False).count(),
            "pending_contact_count": ContactMessage.objects.filter(is_resolved=False).count(),
        }
    return {}
