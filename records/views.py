from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

from records.utils import check_feed_levels_and_notify
from .forms import WorkerSignUpForm
from .models import CustomUser, EggRecord, FeedPurchase, FeedRecord, SaleRecord
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import redirect

def signup_view(request):
    if request.method == 'POST':
        form = WorkerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'worker'  # Automatically set role
            user.save()
            login(request, user)
            return redirect('worker_dashboard')
    else:
        form = WorkerSignUpForm()
    return render(request, 'records/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'worker':
                return redirect('worker_dashboard')
            else:
                return redirect('admin_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'records/login.html', {'form': form})




from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum
from .forms import EggRecordForm, FeedRecordForm, SaleRecordForm
from .models import EggRecord, FeedRecord, SaleRecord
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
def worker_dashboard(request):
    user = request.user
    today = timezone.now().date()

    # Initialize forms
    egg_form = EggRecordForm()
    feed_form = FeedRecordForm()
    sale_form = SaleRecordForm()

    # --- TOTALS SOLD SO FAR (ALL-TIME) ---
    egg_sales_total = SaleRecord.objects.filter(worker=user, product='egg').aggregate(
        total_crates=Sum('crates'),
        total_pieces=Sum('pieces')
    )
    other_sales_total = (
        SaleRecord.objects.filter(worker=user)
        .exclude(product='egg')
        .values('product')
        .annotate(total_quantity=Sum('quantity'))
    )

    # --- TODAY'S SALES TOTALS ---
    egg_sales_today = SaleRecord.objects.filter(worker=user, date=today, product='egg').aggregate(
        total_crates=Sum('crates'),
        total_pieces=Sum('pieces')
    )
    other_sales_today = (
        SaleRecord.objects.filter(worker=user, date=today)
        .exclude(product='egg')
        .values('product')
        .annotate(total_quantity=Sum('quantity'))
    )

    # --- FEED TOTALS TODAY (BY WORKER) ---
    feed_totals_today = (
        FeedRecord.objects.filter(worker=user, date=today)
        .values('animal_category')
        .annotate(total_quantity=Sum('quantity'))
    )

    # --- ALL-TIME FEED TOTALS (BY WORKER) ---
    feed_totals_all = (
        FeedRecord.objects.filter(worker=user)
        .values('animal_category')
        .annotate(total_quantity=Sum('quantity'))
    )

    # --- FEED HISTORY (all records, most recent first) ---
    feed_records = FeedRecord.objects.filter(worker=user).order_by('-date', '-id')

    # --- INDIVIDUAL SALE HISTORY (ALL SALES) ---
    sale_records = SaleRecord.objects.filter(worker=user).order_by('-date', '-id')

    # --- HANDLE FORM SUBMISSIONS ---
    if request.method == "POST":
        if "egg_submit" in request.POST:
            egg_form = EggRecordForm(request.POST)
            if egg_form.is_valid():
                record = egg_form.save(commit=False)
                record.worker = user
                record.save()

                subject = "New Egg Record Submitted"
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [settings.ADMIN_EMAIL]

                context = {
                    "worker": user,
                    "record": record,
                }

                text_content = render_to_string("emails/egg_record.txt", context)
                html_content = render_to_string("emails/egg_record.html", context)

                msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                return redirect('worker_dashboard')

        elif "feed_submit" in request.POST:
            feed_form = FeedRecordForm(request.POST)
            if feed_form.is_valid():
                record = feed_form.save(commit=False)
                record.worker = user
                record.save()
                check_feed_levels_and_notify()
                return redirect('worker_dashboard')

        elif "sale_submit" in request.POST:
            sale_form = SaleRecordForm(request.POST)
            if sale_form.is_valid():
                record = sale_form.save(commit=False)
                record.worker = user
                record.save()

                # ---- Send email notification ----
                subject = "New Sale Record Submitted"
                from_email = settings.DEFAULT_FROM_EMAIL
                to = [settings.ADMIN_EMAIL]

                context = {
                    "worker": user,
                    "record": record
                }

                text_content = render_to_string("emails/sale_record.txt", context)
                html_content = render_to_string("emails/sale_record.html", context)

                msg = EmailMultiAlternatives(subject, text_content, from_email, to)
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                return redirect("worker_dashboard")

    egg_records = EggRecord.objects.filter(worker=user).order_by('-date', '-id')

    feed_purchased = (
        FeedPurchase.objects.values("animal_category")
        .annotate(total_bags=Sum("quantity_bags"))
    )

    feed_used = (
        FeedRecord.objects.values("animal_category")
        .annotate(total_used=Sum("quantity"))
    )

    # Convert into dicts for lookup
    feed_purchased_dict = {item["animal_category"]: item["total_bags"] for item in feed_purchased}
    feed_used_dict = {item["animal_category"]: item["total_used"] for item in feed_used}

    # Calculate remaining stock
    feed_remaining = {}
    for category, total_purchased in feed_purchased_dict.items():
        used = feed_used_dict.get(category, 0)
        feed_remaining[category] = total_purchased - used


    context = {
        'egg_form': egg_form,
        'feed_form': feed_form,
        'sale_form': sale_form,
        'egg_sales_total': egg_sales_total,
        'other_sales_total': other_sales_total,
        'egg_sales_today': egg_sales_today,
        'other_sales_today': other_sales_today,
        'sale_records': sale_records,
        'today': today,
        'feed_totals_today': feed_totals_today,
        'feed_totals_all': feed_totals_all,
        'feed_records': feed_records,
        'egg_records': egg_records, 
        'feed_remaining': feed_remaining,   # 👈 add this
    }

    return render(request, 'records/worker_dashboard.html', context)


def home_view(request):
    return render(request, 'records/home.html')


from django.contrib.auth import logout
def user_logout(request):
    logout(request)
    return redirect('login') 