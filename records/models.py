from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from decimal import Decimal


# ---------- Custom User ----------
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # Ensure admin role

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('worker', 'Worker'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='worker')
    name = models.CharField(max_length=100)

    objects = CustomUserManager()

    def __str__(self):
        return self.username


# ---------- Egg Production ----------
class EggRecord(models.Model):
    worker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    crates = models.PositiveIntegerField()
    pieces = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.worker.name} - {self.date} - {self.crates} crates + {self.pieces} pcs"


# ---------- Feed Intake ----------
class FeedRecord(models.Model):
    ANIMAL_CHOICES = [
        ('laying_bird', 'Laying Bird'),
        ('young_layer', 'Young Layer'),
        ('cow', 'Cow'),
        ('goat', 'Goat'),
        ('pig', 'Pig'),
    ]

    worker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    animal_category = models.CharField(max_length=20, choices=ANIMAL_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                   help_text="Bags for birds, Kg for others")

    def __str__(self):
        return f"{self.worker.name} - {self.animal_category} - {self.quantity}"


# ---------- Sales Record ----------
class SaleRecord(models.Model):
    PRODUCT_CHOICES = [
        ('egg', 'Egg'),
        ('milk', 'Milk'),
        ('meat', 'Meat'),
        ('other', 'Other'),
    ]

    worker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    product = models.CharField(max_length=20, choices=PRODUCT_CHOICES)
    crates = models.PositiveIntegerField(default=0)
    pieces = models.PositiveIntegerField(default=0)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                   default=Decimal('0.00'),
                                   help_text="Kg or units for non-egg products")

    unit_price = models.DecimalField(max_digits=10, decimal_places=2,
                                     default=Decimal('0.00'))
    price_per_crate = models.DecimalField(max_digits=10, decimal_places=2,
                                          default=Decimal('0.00'))

    def __str__(self):
        if self.product == 'egg':
            return f"{self.worker.name} - {self.product} - {self.crates} crates + {self.pieces} pcs at ₦{self.price_per_crate}"
        return f"{self.worker.name} - {self.product} - {self.quantity}"


# ---------- Feed Purchase ----------
class FeedPurchase(models.Model):
    ANIMAL_CHOICES = [
        ('laying_bird', 'Laying Bird'),
        ('young_layer', 'Young Layer'),
        ('cow', 'Cow'),
        ('goat', 'Goat'),
        ('pig', 'Pig'),
    ]

    animal_category = models.CharField(max_length=20, choices=ANIMAL_CHOICES)
    quantity_bags = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_bag = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.quantity_bags * self.price_per_bag

    def __str__(self):
        return f"{self.animal_category} - {self.quantity_bags} bags @ {self.price_per_bag} each"


# ---------- Expense ----------
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('vaccine', 'Vaccine'),
        ('repair', 'Repair'),
        ('transportation', 'Transportation'),
        ('other', 'Other'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"
