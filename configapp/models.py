from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class ResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        now = timezone.now()
        diff = now - self.created_at
        return diff.total_seconds() < 120

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100, default='')
    symbol = models.CharField(max_length=10, default='')
    rate = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return self.code

class Account(models.Model):
    TYPES = (
        ('CASH', 'Cash'),
        ('CARD', 'Card')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPES)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} ({self.currency.code})"

class Budget(models.Model):
    TYPES = (
        ('MONTHLY', 'Monthly'),
        ('STIPEND', 'Stipend'),
        ('OTHER', 'Other')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, choices=TYPES)
    category = models.CharField(max_length=100)
    amount_limit = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    month = models.IntegerField(default=timezone.now().month)
    year = models.IntegerField(default=timezone.now().year)

    def __str__(self):
        return f"{self.category} - {self.month}/{self.year}"

class Transaction(models.Model):
    TYPES = (
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense')
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPES)
    category = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type}: {self.amount}"

class RecurringTransaction(models.Model):
    FREQUENCIES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly')
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    type = models.CharField(max_length=10, choices=Transaction.TYPES)
    category = models.CharField(max_length=100)
    frequency = models.CharField(max_length=10, choices=FREQUENCIES)
    next_date = models.DateField()

class FinancialGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=20, decimal_places=2)
    current_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

    def get_progress_percent(self):
        if self.target_amount <= 0:
            return 0
        percent = (self.current_amount / self.target_amount) * 100
        return int(min(percent, 100))

    def __str__(self):
        return self.title