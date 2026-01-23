from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views import View
from django.views.generic import ListView, TemplateView
from decimal import Decimal
import random
from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction, Budget
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer

User = get_object_or_404(get_user_model()) if False else get_user_model()

class HomeView(TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return redirect('admin_panel')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        current_time = timezone.now()

        recurring = RecurringTransaction.objects.filter(next_date__lte=today, account__user=user)
        for item in recurring:
            if item.type == 'EXPENSE' and item.account.balance < item.amount:
                continue
            Transaction.objects.create(
                account=item.account, amount=item.amount, type=item.type,
                category=f"{_('Auto')}: {item.category}"
            )
            if item.type == 'INCOME': item.account.balance += item.amount
            else: item.account.balance -= item.amount
            item.account.save()
            days = 30 if item.frequency == 'MONTHLY' else 7
            item.next_date += timezone.timedelta(days=days)
            item.save()

        selected_code = self.request.GET.get('currency', 'UZS')
        target_currency = Currency.objects.filter(code=selected_code).first() or \
                          Currency.objects.filter(code='UZS').first() or Currency.objects.first()

        accounts = Account.objects.filter(user=user)
        total_balance = Decimal('0.00')
        category_totals = {}
        for acc in accounts:
            total_balance += (acc.balance * acc.currency.rate / target_currency.rate)
            for t in Transaction.objects.filter(account=acc, type='EXPENSE'):
                conv = t.amount * acc.currency.rate / target_currency.rate
                category_totals[t.category] = category_totals.get(t.category, Decimal('0')) + conv

        budgets = Budget.objects.filter(user=user, month=current_time.month, year=current_time.year)
        budget_data = []
        for b in budgets:
            spent = Transaction.objects.filter(
                account__user=user, category=b.category, type='EXPENSE',
                date__month=current_time.month, date__year=current_time.year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            budget_data.append({
                'info': b, 'spent': spent,
                'percent': int((spent / b.amount_limit) * 100) if b.amount_limit > 0 else 0
            })

        context.update({
            'accounts': accounts, 'goals': FinancialGoal.objects.filter(user=user),
            'total': total_balance, 'selected_currency': target_currency,
            'all_currencies': Currency.objects.all(),
            'chart_labels': list(category_totals.keys()),
            'chart_data': [float(v) for v in category_totals.values()],
            'budgets': budget_data,
        })
        return context

class TransactionHistoryView(ListView):
    model = Transaction
    template_name = 'history.html'
    context_object_name = 'transactions'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Transaction.objects.filter(account__user=self.request.user).order_by('-date')
        t_type = self.request.GET.get('type')
        search = self.request.GET.get('search')
        if t_type: qs = qs.filter(type=t_type)
        if search: qs = qs.filter(category__icontains=search)
        return qs

class BudgetListView(TemplateView):
    template_name = 'budgets.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budgets = Budget.objects.filter(user=self.request.user)
        budget_data = []
        for budget in budgets:
            related_transactions = Transaction.objects.filter(
                account__user=self.request.user, category__iexact=budget.category,
                type='EXPENSE', date__month=budget.month, date__year=budget.year
            ).order_by('-date')
            total_spent = sum((t.amount / t.account.currency.rate) * budget.currency.rate for t in related_transactions)
            budget_data.append({
                'info': budget, 'transactions': related_transactions,
                'total_spent': round(total_spent, 2),
                'percent': int((total_spent / budget.amount_limit) * 100) if budget.amount_limit > 0 else 0
            })
        context['budget_data'] = budget_data
        return context

class GoalsHistoryView(ListView):
    model = Transaction
    template_name = 'goals_history.html'
    context_object_name = 'transactions'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user, category__startswith="Goal:").order_by('-date')

class AddTransactionView(View):
    def post(self, request):
        if not request.user.is_authenticated: return redirect('login')
        account = get_object_or_404(Account, id=request.POST.get('account'), user=request.user)
        amount = Decimal(request.POST.get('amount', '0'))
        t_type = request.POST.get('type')
        category = request.POST.get('category').strip()
        if t_type == 'EXPENSE' and account.balance < amount:
            messages.error(request, _("Insufficient funds!"))
            return redirect('home')
        if t_type == 'INCOME': account.balance += amount
        else: account.balance -= amount
        account.save()
        Transaction.objects.create(account=account, amount=amount, type=t_type, category=category)
        messages.success(request, _("Transaction saved!"))
        return redirect('home')

class ContributeToGoalView(View):
    def post(self, request):
        if not request.user.is_authenticated: return redirect('login')
        goal = get_object_or_404(FinancialGoal, id=request.POST.get('goal'), user=request.user)
        account = get_object_or_404(Account, id=request.POST.get('account'), user=request.user)
        amount = Decimal(request.POST.get('amount', '0'))
        if account.balance >= amount:
            account.balance -= amount
            account.save()
            converted = (amount * account.currency.rate) / goal.currency.rate
            goal.current_amount += converted
            goal.save()
            Transaction.objects.create(account=account, amount=amount, type='EXPENSE', category=f"{_('Goal')}: {goal.title}")
            messages.success(request, _("Funds added to goal!"))
        else:
            messages.error(request, _("Insufficient funds!"))
        return redirect('home')

class AddAccountView(View):
    def post(self, request):
        if not request.user.is_authenticated: return redirect('login')
        Account.objects.create(
            user=request.user, name=request.POST.get('name'),
            balance=Decimal(request.POST.get('balance', '0')),
            currency=get_object_or_404(Currency, id=request.POST.get('currency'))
        )
        messages.success(request, _("Account added successfully!"))
        return redirect('home')

class AddBudgetView(View):
    def post(self, request):
        if not request.user.is_authenticated: return redirect('login')
        Budget.objects.create(
            user=request.user, name=request.POST.get('name'),
            category=request.POST.get('category'),
            amount_limit=Decimal(request.POST.get('limit', '0')),
            currency=get_object_or_404(Currency, id=request.POST.get('currency'))
        )
        messages.success(request, _("Budget created!"))
        return redirect('home')

class AddGoalView(View):
    def post(self, request):
        if not request.user.is_authenticated: return redirect('login')
        FinancialGoal.objects.create(
            user=request.user, title=request.POST.get('title'),
            target_amount=Decimal(request.POST.get('target', '0')),
            currency=get_object_or_404(Currency, id=request.POST.get('currency'))
        )
        messages.success(request, _("Goal added!"))
        return redirect('home')

class LoginView(View):
    def get(self, request): return render(request, 'login.html')
    def post(self, request):
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('admin_panel' if user.is_superuser else 'home')
        messages.error(request, _("Invalid email or password!"))
        return render(request, 'login.html')

class RegisterView(View):
    def get(self, request): return render(request, 'register.html')
    def post(self, request):
        email = request.POST.get('email')
        p, c = request.POST.get('password'), request.POST.get('confirm_password')
        if p == c and not User.objects.filter(email=email).exists():
            user = User.objects.create_user(email=email, password=p, username=email)
            login(request, user)
            return redirect('home')
        messages.error(request, _("Passwords do not match or user already exists!"))
        return render(request, 'register.html')

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class ForgotPasswordView(View):
    def get(self, request): return render(request, 'forgot_password.html')
    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            code = str(random.randint(100000, 999999))
            ResetCode.objects.create(user=user, code=code)
            send_mail(_('Reset Code'), f"{_('Your verification code')}: {code}", settings.EMAIL_HOST_USER, [email])
            return redirect('verify_code', user_id=user.id)
        messages.error(request, _("User with this email not found!"))
        return render(request, 'forgot_password.html')

class VerifyCodeView(View):
    def get(self, request, user_id): return render(request, 'verify_code.html')
    def post(self, request, user_id):
        reset = ResetCode.objects.filter(user_id=user_id, code=request.POST.get('code')).last()
        if reset and reset.is_valid():
            reset.user.set_password(request.POST.get('password'))
            reset.user.save()
            messages.success(request, _("Password updated!"))
            return redirect('login')
        messages.error(request, _("Invalid code!"))
        return render(request, 'verify_code.html')

class AdminDashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('login')
        context = {
            'total_users': User.objects.filter(is_superuser=False).count(),
            'users_list': User.objects.filter(is_superuser=False).prefetch_related('account_set'),
            'recent_transactions': Transaction.objects.all().order_by('-date')[:10],
        }
        return render(request, 'admin_custom.html', context)

class DeleteUserView(View):
    def post(self, request, user_id):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('login')
        User.objects.filter(id=user_id, is_superuser=False).delete()
        messages.success(request, _("User deleted successfully!"))
        return redirect('admin_panel')

class AccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = AccountSerializer(Account.objects.filter(user=request.user), many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = AccountSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs = Transaction.objects.filter(account__user=request.user).order_by('-date')
        return Response(TransactionSerializer(qs, many=True).data)

class GoalAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = GoalSerializer(FinancialGoal.objects.filter(user=request.user), many=True)
        return Response(serializer.data)