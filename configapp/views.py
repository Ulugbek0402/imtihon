from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
import random
from django.contrib.auth.forms import PasswordChangeForm

from .models import Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction, Budget
from rest_framework import viewsets
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer

User = get_user_model()

def is_admin(user):
    return user.is_superuser

@login_required(login_url='login')
def home_view(request):
    if request.user.is_superuser:
        return redirect('admin_panel')

    today = timezone.now().date()
    recurring = RecurringTransaction.objects.filter(next_date__lte=today, account__user=request.user)
    for item in recurring:
        if item.type == 'EXPENSE' and item.account.balance < item.amount:
            continue

        Transaction.objects.create(
            account=item.account, amount=item.amount,
            type=item.type, category=f"Auto: {item.category}"
        )
        if item.type == 'INCOME':
            item.account.balance += item.amount
        else:
            item.account.balance -= item.amount
        item.account.save()

        days = 30 if item.frequency == 'MONTHLY' else 7
        item.next_date += timezone.timedelta(days=days)
        item.save()

    selected_code = request.GET.get('currency', 'UZS')
    target_currency = Currency.objects.filter(code=selected_code).first() or  \
                      Currency.objects.filter(code='UZS').first() or Currency.objects.first()

    accounts = Account.objects.filter(user=request.user)
    goals = FinancialGoal.objects.filter(user=request.user)

    budgets = Budget.objects.filter(user=request.user, month=today.month, year=today.year)
    budget_data = []
    for b in budgets:
        spent = Transaction.objects.filter(
            account__user=request.user, category=b.category, type='EXPENSE',
            date__month=today.month, date__year=today.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        budget_data.append({
            'info': b, 'spent': spent,
            'percent': int((spent / b.amount_limit) * 100) if b.amount_limit > 0 else 0
        })

    total_balance = Decimal('0.00')
    category_totals = {}
    for acc in accounts:
        acc_rate = acc.currency.rate
        total_balance += (acc.balance * acc_rate / target_currency.rate)
        acc_transactions = Transaction.objects.filter(account=acc, type='EXPENSE')
        for t in acc_transactions:
            converted_amount = t.amount * acc_rate / target_currency.rate
            category_totals[t.category] = category_totals.get(t.category, Decimal('0')) + converted_amount

    return render(request, 'home.html', {
        'accounts': accounts, 'goals': goals, 'total': total_balance,
        'selected_currency': target_currency, 'all_currencies': Currency.objects.all(),
        'chart_labels': list(category_totals.keys()),
        'chart_data': [float(v) for v in category_totals.values()],
        'budgets': budget_data,
    })

@login_required(login_url='login')
def add_transaction(request):
    if request.method == "POST":
        account_id = request.POST.get('account')
        amount = Decimal(request.POST.get('amount', '0'))
        t_type = request.POST.get('type')
        category = request.POST.get('category')
        account = get_object_or_404(Account, id=account_id, user=request.user)

        if t_type == 'EXPENSE':
            if account.balance < amount:
                messages.error(request, "Mablag' yetarli emas!")
                return redirect('home')
            today = timezone.now()
            budget = Budget.objects.filter(user=request.user, category=category, month=today.month, year=today.year).first()
            if budget:
                spent = Transaction.objects.filter(account__user=request.user, category=category, type='EXPENSE' , \
                                                   date__month=today.month).aggregate(s=Sum('amount'))['s'] or 0
                if (spent + amount) > budget.amount_limit:
                    messages.warning(request, f"{category} uchun byudjet limitidan oshdingiz!")

        if t_type == 'INCOME':
            account.balance += amount
        else:
            account.balance -= amount
        account.save()
        Transaction.objects.create(account=account, amount=amount, type=t_type, category=category)
        messages.success(request, "Tranzaksiya saqlandi!")
    return redirect('home')


@login_required(login_url='login')
def add_budget(request):
    if request.method == "POST":
        name = request.POST.get('name')
        category = request.POST.get('category')
        limit = Decimal(request.POST.get('limit', '0'))
        currency = get_object_or_404(Currency, id=request.POST.get('currency'))

        Budget.objects.create(
            user=request.user,
            name=name,
            category=category,
            amount_limit=limit,
            currency=currency,
        )
        messages.success(request, "Byudjet belgilandi!")
    return redirect('home')

@login_required(login_url='login')
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user)
    budget_data = []

    for budget in budgets:
        related_transactions = Transaction.objects.filter(
            account__user=request.user,
            category__iexact=budget.category,
            type='EXPENSE'
        ).order_by('-date')

        total_spent_in_budget_currency = 0

        for t in related_transactions:
            if t.account.currency != budget.currency:
                converted_amount = (t.amount * t.account.currency.rate) / budget.currency.rate
                total_spent_in_budget_currency += round(converted_amount, 2)
            else:
                total_spent_in_budget_currency += t.amount

        budget_data.append({
            'info': budget,
            'transactions': related_transactions,
            'total_spent': total_spent_in_budget_currency
        })

    return render(request, 'budgets.html', {'budget_data': budget_data})

@login_required(login_url='login')
def add_goal(request):
    if request.method == "POST":
        title = request.POST.get('title')
        target = Decimal(request.POST.get('target', '0'))
        currency_id = request.POST.get('currency')
        currency = get_object_or_404(Currency, id=currency_id)

        FinancialGoal.objects.create(
            user=request.user,
            title=title,
            target_amount=target,
            currency=currency
        )
        messages.success(request, "Yangi maqsad muvaffaqiyatli qo'shildi!")
    return redirect('home')

@login_required(login_url='login')
def contribute_to_goal(request):
    if request.method == "POST":
        goal = get_object_or_404(FinancialGoal, id=request.POST.get('goal'), user=request.user)
        account = get_object_or_404(Account, id=request.POST.get('account'), user=request.user)
        amount = Decimal(request.POST.get('amount', '0'))
        if account.balance >= amount:
            account.balance -= amount
            account.save()
            goal.current_amount += (amount * account.currency.rate / goal.currency.rate)
            goal.save()
            Transaction.objects.create(account=account, amount=amount, type='EXPENSE', category=f"Goal: {goal.title}")
            messages.success(request, "Maqsadga pul qo'shildi!")
        else:
            messages.error(request, "Mablag' yetarli emas!")
    return redirect('home')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_panel') if request.user.is_superuser else redirect('home')
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('admin_panel') if user.is_superuser else redirect('home')
        messages.error(request, "Xato!")
    return render(request, 'login.html')

def register_view(request):
    if request.method == "POST":
        email, p, c = request.POST.get('email'), request.POST.get('password'), request.POST.get('confirm_password')
        if p == c and not User.objects.filter(email=email).exists():
            user = User.objects.create_user(email=email, password=p, username=email)
            login(request, user)
            return redirect('home')
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def history_view(request):
    transactions = Transaction.objects.filter(account__user=request.user).order_by('-date')

    t_type = request.GET.get('type')
    if t_type:
        transactions = transactions.filter(type=t_type)

    search_query = request.GET.get('search')
    if search_query:
        transactions = transactions.filter(category__icontains=search_query)

    return render(request, 'history.html', {'transactions': transactions})


@login_required(login_url='login')
def goals_history(request):
    goal_transactions = Transaction.objects.filter(
        account__user=request.user,
        category__startswith="Goal:"
    ).order_by('-date')

    return render(request, 'goals_history.html', {'transactions': goal_transactions})

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'admin_custom.html', {
        'total_users': User.objects.filter(is_superuser=False).count(),
        'total_accounts': Account.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'users_list': User.objects.filter(is_superuser=False).prefetch_related('account_set'),
        'recent_transactions': Transaction.objects.all().order_by('-date')[:10],
    })

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_manage_model(request, model_name):
    maps = {'accounts': (Account, ['User', 'Name', 'Balance', 'Currency']), \
            'transactions': (Transaction, ['Account', 'Amount', 'Type', 'Category']), 'currencies': \
                (Currency, ['Name', 'Code', 'Rate']), 'goals': (FinancialGoal, ['User', 'Title', 'Target', 'Current'])}
    model, cols = maps.get(model_name)
    return render(request, 'admin_model_list.html', {'data': model.objects.all(), \
                                                     'model_name': model_name.capitalize(), 'columns': cols})

@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_user(request, user_id):
    User.objects.filter(id=user_id, is_superuser=False).delete()
    return redirect('admin_panel')

@login_required(login_url='login')
def add_account(request):
    if request.method == "POST":
        Account.objects.create(user=request.user, name=request.POST.get('name'), \
                               balance=Decimal(request.POST.get('balance', '0')), \
                               currency=get_object_or_404(Currency, id=request.POST.get('currency')))
    return redirect('home')


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            code = str(random.randint(100000, 999999))
            ResetCode.objects.create(user=user, code=code)

            subject = 'FinanceHome - Parolni tiklash kodi'
            message = f'Sizning tasdiqlash kodingiz: {code}. Ushbu kod 10 daqiqa davomida amal qiladi.'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email]

            try:
                send_mail(subject, message, email_from, recipient_list)
                messages.success(request, "Kod emailingizga yuborildi!")
                return redirect('verify_code', user_id=user.id)
            except Exception as e:
                messages.error(request, f"Email yuborishda xatolik: {str(e)}")
        else:
            messages.error(request, "Bunday email bilan foydalanuvchi topilmadi.")

    return render(request, 'forgot_password.html')

def verify_code(request, user_id):
    if request.method == "POST":
        reset = ResetCode.objects.filter(user_id=user_id, code=request.POST.get('code')).last()
        if reset and reset.is_valid():
            reset.user.set_password(request.POST.get('password'))
            reset.user.save()
            return redirect('login')
    return render(request, 'verify_code.html')


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Parolingiz muvaffaqiyatli o'zgartirildi!")
            return redirect('home')
        else:
            messages.error(request, "Iltimos, xatolarni tuzating.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    def get_queryset(self): return Account.objects.filter(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    def get_queryset(self): return Transaction.objects.filter(account__user=self.request.user)

class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    def get_queryset(self): return FinancialGoal.objects.filter(user=self.request.user)