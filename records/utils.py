
from decimal import Decimal
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import FeedPurchase, FeedRecord

def check_feed_levels_and_notify():
    feed_used = (
        FeedRecord.objects.values("animal_category")
        .annotate(
            total_used=Coalesce(
                Sum("quantity", output_field=DecimalField(max_digits=12, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )
    )
    feed_used_dict = {item["animal_category"]: item["total_used"] for item in feed_used}

    feed_summary_qs = (
        FeedPurchase.objects.values("animal_category")
        .annotate(
            total_bought=Coalesce(
                Sum("quantity_bags", output_field=DecimalField(max_digits=12, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )
    )

    feed_summary = {}
    low_stock_alerts = []

    for item in feed_summary_qs:
        category = item["animal_category"]
        bought = Decimal(item["total_bought"] or 0)
        used = Decimal(feed_used_dict.get(category, 0) or 0)
        available = bought - used if bought > used else Decimal("0")

        feed_summary[category] = {
            "total_purchased": bought,
            "total_used": used,
            "remaining": available,
        }

        if available <= 3:
            low_stock_alerts.append({
                "category": category,
                "remaining": available
            })

    if low_stock_alerts:
        subject = "⚠️ Feed Low Stock Alert"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [settings.ADMIN_EMAIL]

        context = {"alerts": low_stock_alerts}
        html_content = render_to_string("emails/feed_low_stock_alert.html", context)
        text_content = render_to_string("emails/feed_low_stock_alert.txt", context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
