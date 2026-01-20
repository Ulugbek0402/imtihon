from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from decimal import Decimal
import random

from .models import Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction
from rest_framework import viewsets
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer

User = get_user_model()


def is_admin(user):
    return user.is_superuser


@login_required(login_url='login')
def home_view(request):
    if request.user.is_superuser:
        return redirect('admin_panel')

    recurring = RecurringTransaction.objects.filter(next_date__lte=timezone.now().date())
    for item in recurring:
        Transaction.objects.create(
            account=item.account, amount=item.amount,
            type=item.type, category="Auto: " + item.category
        )
        item.next_date += timezone.timedelta(days=30 if item.frequency == 'MONTHLY' else 7)
        item.save()

    selected_code = request.GET.get('currency', 'UZS')
    target_currency = Currency.objects.filter(code=selected_code).first() or Currency.objects.filter(
        code='UZS').first() or Currency.objects.first()

    accounts = Account.objects.filter(user=request.user)
    goals = FinancialGoal.objects.filter(user=request.user)

    total_balance = Decimal('0.00')
    category_totals = {}

    for acc in accounts:
        acc_rate = acc.currency.rate
        total_balance += (acc.balance * acc_rate / target_currency.rate)

        acc_transactions = Transaction.objects.filter(account=acc, type='EXPENSE')
        for t in acc_transactions:
            converted_amount = t.amount * acc_rate / target_currency.rate
            category_totals[t.category] = category_totals.get(t.category, Decimal('0')) + converted_amount

    chart_labels = list(category_totals.keys())
    chart_data = [float(amount) for amount in category_totals.values()]

    return render(request, 'home.html', {
        'accounts': accounts, 'goals': goals, 'total': total_balance,
        'selected_currency': target_currency, 'all_currencies': Currency.objects.all(),
        'chart_labels': chart_labels, 'chart_data': chart_data,
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'total_users': User.objects.filter(is_superuser=False).count(),
        'total_accounts': Account.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'users_list': User.objects.filter(is_superuser=False).prefetch_related('account_set'),
        'recent_transactions': Transaction.objects.all().order_by('-date')[:10],
    }
    return render(request, 'admin_custom.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_manage_model(request, model_name):
    data = []
    columns = []
    if model_name == 'accounts':
        data = Account.objects.all()
        columns = ['User', 'Name', 'Balance', 'Currency']
    elif model_name == 'transactions':
        data = Transaction.objects.all().order_by('-date')
        columns = ['Account', 'Amount', 'Type', 'Category', 'Date']
    elif model_name == 'currencies':
        data = Currency.objects.all()
        columns = ['Name', 'Code', 'Symbol', 'Rate']
    elif model_name == 'goals':
        data = FinancialGoal.objects.all()
        columns = ['User', 'Title', 'Target', 'Current']
    return render(request, 'admin_model_list.html', {
        'data': data,
        'model_name': model_name.capitalize(),
        'columns': columns
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_superuser:
        user.delete()
        messages.success(request, "User deleted.")
    return redirect('admin_panel')


@login_required(login_url='login')
def add_account(request):
    if request.method == "POST":
        name = request.POST.get('name')
        balance = Decimal(request.POST.get('balance', '0'))
        currency_id = request.POST.get('currency')
        try:
            currency = Currency.objects.get(id=currency_id)
            Account.objects.create(user=request.user, name=name, balance=balance, currency=currency)
            messages.success(request, "Account created!")
        except:
            messages.error(request, "Error creating account!")
    return redirect('home')


@login_required(login_url='login')
def add_transaction(request):
    if request.method == "POST":
        account_id = request.POST.get('account')
        amount = Decimal(request.POST.get('amount', '0'))
        t_type = request.POST.get('type')
        category = request.POST.get('category')
        account = get_object_or_404(Account, id=account_id, user=request.user)

        if t_type == 'EXPENSE' and account.balance < amount:
            messages.error(request, "Hisobingizda mablag' yetarli emas!")
            return redirect('home')

        if t_type == 'INCOME':
            account.balance += amount
        else:
            account.balance -= amount

        account.save()
        Transaction.objects.create(account=account, amount=amount, type=t_type, category=category)
        messages.success(request, "Transaction saved!")
    return redirect('home')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_panel') if request.user.is_superuser else redirect('home')
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_panel') if user.is_superuser else redirect('home')
        messages.error(request, "Invalid login!")
    return render(request, 'login.html')


def register_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        if password == confirm:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(email=email, password=password, username=email)
                login(request, user)
                return redirect('home')
            messages.error(request, "Email already exists!")
        else:
            messages.error(request, "Passwords mismatch!")
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def history_view(request):
    transactions = Transaction.objects.filter(account__user=request.user).order_by('-date')
    return render(request, 'history.html', {'transactions': transactions})


@login_required(login_url='login')
def contribute_to_goal(request):
    if request.method == "POST":
        goal = get_object_or_404(FinancialGoal, id=request.POST.get('goal'), user=request.user)
        account = get_object_or_404(Account, id=request.POST.get('account'), user=request.user)
        amount = Decimal(request.POST.get('amount', '0'))

        if account.balance >= amount:
            account.balance -= amount
            account.save()
            goal.current_amount += amount
            goal.save()
            Transaction.objects.create(account=account, amount=amount, type='EXPENSE', category=f"Goal: {goal.title}")
            messages.success(request, "Goal updated!")
        else:
            messages.error(request, "Hisobda mablag' yetarli emas!")
    return redirect('home')


def forgot_password(request):
    if request.method == "POST":
        user = User.objects.filter(email=request.POST.get('email')).first()
        if user:
            code = str(random.randint(100000, 999999))
            ResetCode.objects.create(user=user, code=code)
            return redirect('verify_code', user_id=user.id)
    return render(request, 'forgot_password.html')


def verify_code(request, user_id):
    if request.method == "POST":
        reset = ResetCode.objects.filter(user_id=user_id, code=request.POST.get('code')).last()
        if reset and reset.is_valid():
            reset.user.set_password(request.POST.get('password'))
            reset.user.save()
            return redirect('login')
    return render(request, 'verify_code.html')


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self): return Account.objects.filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self): return Transaction.objects.filter(account__user=self.request.user)


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer

    def get_queryset(self): return FinancialGoal.objects.filter(user=self.request.user)