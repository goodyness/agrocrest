from decimal import Decimal
from datetime import date
from django.shortcuts import render, redirect
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings

from .models import EggRecord, FeedPurchase, FeedRecord, SaleRecord, Expense
from .forms import FeedPurchaseForm, ExpenseForm
from django.db.models import Value, IntegerField, DecimalField
from django.utils.timezone import now

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


from decimal import Decimal
from django.db.models import Sum, F, Value, ExpressionWrapper, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from datetime import date

from .models import FeedPurchase, FeedRecord, SaleRecord, Expense
from .forms import FeedPurchaseForm, ExpenseForm


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = date.today()

    feed_form = FeedPurchaseForm()
    expense_form = ExpenseForm()

    if request.method == "POST":
        if "feed_submit" in request.POST:
            feed_form = FeedPurchaseForm(request.POST)
            if feed_form.is_valid():
                feed_form.save()
                return redirect("admin_dashboard")

        elif "expense_submit" in request.POST:
            expense_form = ExpenseForm(request.POST)
            if expense_form.is_valid():
                expense_form.save()
                return redirect("admin_dashboard")

    feed_purchases = FeedPurchase.objects.all().order_by("-date", "-id")

    feed_used = (
        FeedRecord.objects.values("animal_category")
        .annotate(
            total_used=Coalesce(
                Sum("quantity", output_field=DecimalField(max_digits=12, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
                output_field=DecimalField(max_digits=12, decimal_places=2),
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
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
    )

    feed_summary = {}
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

    # --- MONTHLY TOTALS ---
    today = now().date()
    this_month_purchases = FeedPurchase.objects.filter(
        date__year=today.year, date__month=today.month
    ).aggregate(
        total_bought=Coalesce(
            Sum("quantity_bags", output_field=DecimalField(max_digits=12, decimal_places=2)),
            Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )

    this_month_used = FeedRecord.objects.filter(
        date__year=today.year, date__month=today.month
    ).aggregate(
        total_used=Coalesce(
            Sum("quantity", output_field=DecimalField(max_digits=12, decimal_places=2)),
            Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )

    total_bought = Decimal(this_month_purchases["total_bought"] or 0)
    total_used = Decimal(this_month_used["total_used"] or 0)
    total_remaining = total_bought - total_used if total_bought > total_used else Decimal("0")

    # --- SALES CALCULATIONS ---
    total_sales_income = Decimal("0")
    sales_summary = []

    for code, label in SaleRecord.PRODUCT_CHOICES:
        records = SaleRecord.objects.filter(product=code)

        if code == "egg":
            crates = records.aggregate(
                total=Coalesce(
                    Sum("crates", output_field=IntegerField()),
                    Value(0, output_field=IntegerField()),
                    output_field=IntegerField(),
                )
            )["total"]

            pieces = records.aggregate(
                total=Coalesce(
                    Sum("pieces", output_field=IntegerField()),
                    Value(0, output_field=IntegerField()),
                    output_field=IntegerField(),
                )
            )["total"]

            income = records.aggregate(
                total=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("crates") * F("price_per_crate"),
                            output_field=DecimalField(max_digits=12, decimal_places=2),
                        )
                    ),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
                )
            )["total"]

            sales_summary.append({
                "product": label,
                "total_crates": crates,
                "total_pieces": pieces,
                "total_income": income,
            })
        else:
            qty = records.aggregate(
                total=Coalesce(
                    Sum("quantity", output_field=DecimalField(max_digits=12, decimal_places=2)),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
                )
            )["total"]

            income = records.aggregate(
                total=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("quantity") * F("unit_price"),
                            output_field=DecimalField(max_digits=12, decimal_places=2),
                        )
                    ),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
                )
            )["total"]

            sales_summary.append({
                "product": label,
                "total_quantity": qty,
                "total_income": income,
            })

        total_sales_income += income or Decimal("0")

    # --- EXPENSES ---
    expenses = Expense.objects.all().order_by("-date")

    total_expenses = Expense.objects.aggregate(
        total=Coalesce(
            Sum("amount", output_field=DecimalField(max_digits=12, decimal_places=2)),
            Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )["total"]

    total_feed_cost = FeedPurchase.objects.aggregate(
        total=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("quantity_bags") * F("price_per_bag"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )["total"]

    # --- PROFIT ---
    profit = total_sales_income - (total_feed_cost + total_expenses)

    # --- EGG PRODUCTION ---
    egg_records = EggRecord.objects.all().order_by("-date", "-id")

    # per-day totals across all workers
    daily_egg_summary = (
        EggRecord.objects.values("date")
        .annotate(
            total_pieces=Coalesce(
                Sum("pieces"), 0, output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            total_crates=Coalesce(
                Sum("crates"), 0, output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
        )
        .order_by("-date")
    )

    # optional: convert crates into pieces (e.g. 1 crate = 30 pieces)
    for item in daily_egg_summary:
        item["total_eggs_in_pieces"] = item["total_pieces"] + (item["total_crates"] * 30)

    context = {
        "feed_form": feed_form,
        "expense_form": expense_form,
        "feed_purchases": feed_purchases,
        "feed_summary": feed_summary,
        "sales_summary": sales_summary,
        "total_feed_cost": total_feed_cost,
        "total_expenses": total_expenses,
        "total_sales_income": total_sales_income,
        "profit": profit,
        "expenses": expenses,
        "total_bought": total_bought,
        "total_used": total_used,
        "total_remaining": total_remaining,
        "this_month": today.strftime("%B %Y"),
        "today": today,
        "daily_egg_summary": daily_egg_summary,
        "egg_records": egg_records,
    }

    return render(request, "records/admin_dashboard.html", context)