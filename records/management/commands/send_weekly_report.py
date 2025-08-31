from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from records.models import FeedPurchase, FeedUsage, Sale, Expense
from django.db.models import Sum, F

class Command(BaseCommand):
    help = "Send weekly farm report to admin"

    def handle(self, *args, **kwargs):
        # Feed data
        feed_purchased = FeedPurchase.objects.values("animal_category") \
            .annotate(total_bags=Sum("bags"))
        feed_used = FeedUsage.objects.values("animal_category") \
            .annotate(total_used=Sum("bags_used"))

        # Calculate remaining feed
        feed_remaining = {}
        for purchase in feed_purchased:
            category = purchase["animal_category"]
            purchased_qty = purchase["total_bags"] or 0
            used_qty = next((u["total_used"] for u in feed_used if u["animal_category"] == category), 0)
            feed_remaining[category] = purchased_qty - used_qty

        # Sales data
        sales_summary = Sale.objects.values("product") \
            .annotate(
                total_crates=Sum("crates"),
                total_pieces=Sum("pieces"),
                total_quantity=Sum("quantity")
            )

        # Financial data
        total_feed_cost = FeedPurchase.objects.aggregate(total=Sum(F("bags") * F("price_per_bag")))["total"] or 0
        total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_sales_income = Sale.objects.aggregate(total=Sum("total_price"))["total"] or 0
        profit = total_sales_income - (total_feed_cost + total_expenses)

        # Render email HTML from a template
        html_message = render_to_string("emails/weekly_report.html", {
            "feed_remaining": feed_remaining,
            "feed_purchased": feed_purchased,
            "feed_used": feed_used,
            "sales_summary": sales_summary,
            "total_feed_cost": total_feed_cost,
            "total_expenses": total_expenses,
            "total_sales_income": total_sales_income,
            "profit": profit,
        })

        subject = "Weekly Farm Report"
        plain_message = "Your farm report for this week is attached."

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            html_message=html_message
        )

        self.stdout.write(self.style.SUCCESS("✅ Weekly report sent successfully!"))
