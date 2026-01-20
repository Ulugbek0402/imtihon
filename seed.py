import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from configapp.models import User, Currency, Account, Transaction, FinancialGoal

def seed_data():
    print("Starting database seeding...")

    user, created = User.objects.get_or_create(email="test@example.com")
    if created:
        user.set_password("password123")
        user.username = "testuser"
        user.save()
        print("- User created: test@example.com / password123")

    uzs, _ = Currency.objects.get_or_create(code="UZS", defaults={'rate': 1})
    usd, _ = Currency.objects.get_or_create(code="USD", defaults={'rate': 12800})
    rub, _ = Currency.objects.get_or_create(code="RUB", defaults={'rate': 140})
    print("- Currencies created (UZS, USD, RUB)")

    acc1, _ = Account.objects.get_or_create(
        user=user, name="Humo Card",
        defaults={'type': 'CARD', 'balance': 5000000, 'currency': uzs}
    )
    acc2, _ = Account.objects.get_or_create(
        user=user, name="Cash Wallet",
        defaults={'type': 'CASH', 'balance': 100, 'currency': usd}
    )
    print("- Accounts created")

    categories = ['Food', 'Transport', 'Rent', 'Shopping', 'Entertainment']
    for _ in range(20):
        Transaction.objects.create(
            account=acc1,
            amount=random.randint(50000, 200000),
            type='EXPENSE',
            category=random.choice(categories),
            date=timezone.now() - timedelta(days=random.randint(0, 30))
        )
    print("- 20 Random transactions created")

    FinancialGoal.objects.get_or_create(
        user=user,
        title="New iPhone",
        defaults={
            'target_amount': 1200,
            'current_amount': 450,
            'currency': usd
        }
    )
    print("- Savings goal created")
    print("Seeding complete! Now run: python manage.py runserver")

if __name__ == "__main__":
    from django.utils import timezone
    seed_data()