from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

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
    rate = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return self.code

class Account(models.Model):
    TYPES = (('CASH', 'Cash'), ('CARD', 'Card'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPES)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

class Budget(models.Model):
    TYPES = (('MONTHLY', 'Monthly'), ('STIPEND', 'Stipend'), ('OTHER', 'Other'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, choices=TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)

class Transaction(models.Model):
    TYPES = (('INCOME', 'Income'), ('EXPENSE', 'Expense'))
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPES)
    category = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

class RecurringTransaction(models.Model):
    FREQUENCIES = (('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'))
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    type = models.CharField(max_length=10, choices=Transaction.TYPES)
    frequency = models.CharField(max_length=10, choices=FREQUENCIES)
    next_date = models.DateField()

class FinancialGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=20, decimal_places=2)
    current_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)