from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from rest_framework import viewsets
from .models import User, Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer
import random


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    recurring = RecurringTransaction.objects.filter(next_date__lte=timezone.now().date())
    for item in recurring:
        Transaction.objects.create(
            account=item.account,
            amount=item.amount,
            type=item.type,
            category="Auto: " + item.category
        )
        if item.frequency == 'MONTHLY':
            item.next_date += timezone.timedelta(days=30)
        else:
            item.next_date += timezone.timedelta(days=7)
        item.save()

    selected_code = request.GET.get('currency', 'UZS')
    target_currency = Currency.objects.filter(code=selected_code).first() or Currency.objects.first()

    accounts = Account.objects.filter(user=request.user)
    goals = FinancialGoal.objects.filter(user=request.user)

    total_balance = 0
    if target_currency:
        for acc in accounts:
            balance_in_base = acc.balance * acc.currency.rate
            total_balance += (balance_in_base / target_currency.rate)

    expenses = Transaction.objects.filter(account__user=request.user, type='EXPENSE').values('category').annotate(
        total=Sum('amount'))
    chart_labels = [item['category'] for item in expenses]
    chart_data = [float(item['total']) for item in expenses]

    return render(request, 'home.html', {
        'accounts': accounts, 'goals': goals, 'total': total_balance,
        'selected_currency': target_currency, 'all_currencies': Currency.objects.all(),
        'chart_labels': chart_labels, 'chart_data': chart_data,
    })


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, "Xato email yoki parol")
    return render(request, 'login.html')


def register_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Bu email band")
        else:
            user = User.objects.create_user(email=email, password=password, username=email.split('@')[0])
            login(request, user)
            return redirect('home')
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            code = str(random.randint(100000, 999999))
            ResetCode.objects.create(user=user, code=code)
            print(f"KOD: {code}")
            return redirect('verify_code', user_id=user.id)
    return render(request, 'forgot_password.html')


def verify_code(request, user_id):
    if request.method == "POST":
        code = request.POST.get('code')
        password = request.POST.get('password')
        reset = ResetCode.objects.filter(user_id=user_id, code=code).last()
        if reset and reset.is_valid():
            user = reset.user
            user.set_password(password)
            user.save()
            return redirect('login')
    return render(request, 'verify_code.html')


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user)


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)