from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none",
            "placeholder": "Enter username"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none",
            "placeholder": "Enter password"
        })
    )


# Sign Up Form
class WorkerSignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none",
            "placeholder": "Enter full name"
        })
        self.fields['username'].widget.attrs.update({
            "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none",
            "placeholder": "Choose a username"
        })
        self.fields['password1'].widget.attrs.update({
            "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none",
            "placeholder": "Enter password"
        })
        self.fields['password2'].widget.attrs.update({
            "class": "w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none",
            "placeholder": "Confirm password"
        })

from django import forms
from .models import EggRecord, FeedRecord, SaleRecord

from django import forms
from decimal import Decimal
from .models import EggRecord, FeedRecord, SaleRecord, FeedPurchase, Expense

tailwind_input = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm " \
                 "focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
tailwind_select = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm " \
                  "focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
tailwind_textarea = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm " \
                    "focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none"

class EggRecordForm(forms.ModelForm):
    class Meta:
        model = EggRecord
        fields = ['crates', 'pieces']
        widgets = {
            'crates': forms.NumberInput(attrs={'class': tailwind_input, 'min': 0}),
            'pieces': forms.NumberInput(attrs={'class': tailwind_input, 'min': 0}),
        }

class FeedRecordForm(forms.ModelForm):
    class Meta:
        model = FeedRecord
        fields = ['animal_category', 'quantity']
        widgets = {
            'animal_category': forms.Select(attrs={'class': tailwind_select}),
            'quantity': forms.NumberInput(attrs={'class': tailwind_input, 'step': 0.5, 'min': 0}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        animal = self.cleaned_data.get('animal_category')

        if animal in ['laying_bird', 'young_layer']:
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than 0")
        else:
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than 0")
            quantity = round(quantity, 2)
        return quantity

class SaleRecordForm(forms.ModelForm):
    class Meta:
        model = SaleRecord
        fields = ['product', 'crates', 'pieces', 'quantity', 'unit_price', 'price_per_crate']
        widgets = {
            'product': forms.Select(attrs={'class': tailwind_select}),
            'crates': forms.NumberInput(attrs={'class': tailwind_input, 'min': 0}),
            'pieces': forms.NumberInput(attrs={'class': tailwind_input, 'min': 0}),
            'quantity': forms.NumberInput(attrs={'class': tailwind_input, 'step': 0.1, 'min': 0}),
            'unit_price': forms.NumberInput(attrs={'class': tailwind_input, 'step': 0.01, 'min': 0}),
            'price_per_crate': forms.NumberInput(attrs={'class': tailwind_input, 'step': 0.01, 'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        crates = cleaned_data.get('crates')
        pieces = cleaned_data.get('pieces')
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        price_per_crate = cleaned_data.get('price_per_crate')

        if product == 'egg':
            if crates is None and pieces is None:
                raise forms.ValidationError("Please enter crates or pieces for eggs.")
            if price_per_crate is None or price_per_crate <= 0:
                raise forms.ValidationError("Please enter a valid price per crate for eggs.")
            cleaned_data['unit_price'] = Decimal('0.00')
        else:
            if quantity is None or quantity <= 0:
                raise forms.ValidationError("Please enter quantity for non-egg products.")
            if unit_price is None or unit_price <= 0:
                raise forms.ValidationError("Please enter a valid unit price for non-egg products.")
            cleaned_data['price_per_crate'] = Decimal('0.00')

        return cleaned_data

class FeedPurchaseForm(forms.ModelForm):
    class Meta:
        model = FeedPurchase
        fields = ['animal_category', 'quantity_bags', 'price_per_bag']
        widgets = {
            'animal_category': forms.Select(attrs={'class': tailwind_select}),
            'quantity_bags': forms.NumberInput(attrs={'class': tailwind_input, 'min': 1}),
            'price_per_bag': forms.NumberInput(attrs={'class': tailwind_input, 'step': 0.01, 'min': 0}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': tailwind_select}),
            'amount': forms.NumberInput(attrs={'class': tailwind_input, 'step': 0.01, 'min': 0}),
            'description': forms.Textarea(attrs={'class': tailwind_textarea, 'rows': 3}),
        }

