from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
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
        messages.success(request, "User deleted successfully.")
    return redirect('admin_panel')


@login_required(login_url='login')
def add_account(request):
    if request.method == "POST":
        name = request.POST.get('name')
        balance = request.POST.get('balance', 0)
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
        amount = float(request.POST.get('amount'))
        t_type = request.POST.get('type')
        category = request.POST.get('category')
        account = get_object_or_404(Account, id=account_id, user=request.user)
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
        if user:
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
                user = User.objects.create_user(email=email, password=password, username=email.split('@')[0])
                login(request, user)
                return redirect('home')
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
        amount = float(request.POST.get('amount'))
        if account.balance >= amount:
            account.balance -= amount
            account.save()
            goal.current_amount += amount
            goal.save()
            Transaction.objects.create(account=account, amount=amount, type='EXPENSE', category=f"Goal: {goal.title}")
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