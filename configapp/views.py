from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, View, CreateView, FormView
from decimal import Decimal
import random

from rest_framework import viewsets, status, permissions
from .models import Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction, Budget
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer

User = get_user_model()


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
            if not (item.type == 'EXPENSE' and item.account.balance < item.amount):
                Transaction.objects.create(
                    account=item.account, amount=item.amount,
                    type=item.type, category=_("Auto: %(category)s") % {'category': item.category}
                )
                if item.type == 'INCOME':
                    item.account.balance += item.amount
                else:
                    item.account.balance -= item.amount
                item.account.save()
                item.next_date += timezone.timedelta(days=30 if item.frequency == 'MONTHLY' else 7)
                item.save()

        selected_code = self.request.GET.get('currency', 'UZS')
        target_currency = Currency.objects.filter(code=selected_code).first() or Currency.objects.first()
        accounts = Account.objects.filter(user=user)

        total_balance = Decimal('0.00')
        category_totals = {}
        for acc in accounts:
            acc_rate = acc.currency.rate
            total_balance += (acc.balance * acc_rate / target_currency.rate)
            for t in Transaction.objects.filter(account=acc, type='EXPENSE'):
                conv = t.amount * acc_rate / target_currency.rate
                category_totals[t.category] = category_totals.get(t.category, Decimal('0')) + conv

        budgets = Budget.objects.filter(user=user, month=current_time.month, year=current_time.year)
        budget_data = []
        for b in budgets:
            spent = Transaction.objects.filter(account__user=user, category=b.category, type='EXPENSE',
                                               date__month=current_time.month, date__year=current_time.year).aggregate(
                total=Sum('amount'))['total'] or Decimal('0')
            budget_data.append({'info': b, 'spent': spent,
                                'percent': int((spent / b.amount_limit) * 100) if b.amount_limit > 0 else 0})

        context.update({
            'accounts': accounts,
            'goals': FinancialGoal.objects.filter(user=user),
            'total': total_balance,
            'selected_currency': target_currency,
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


class AddTransactionView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        account = get_object_or_404(Account, id=request.POST.get('account'), user=request.user)
        amount = Decimal(request.POST.get('amount', '0'))
        t_type = request.POST.get('type')
        category = request.POST.get('category').strip()
        if t_type == 'EXPENSE' and account.balance < amount:
            messages.error(request, _("Insufficient funds!"))
        else:
            if t_type == 'INCOME':
                account.balance += amount
            else:
                account.balance -= amount
            account.save()
            Transaction.objects.create(account=account, amount=amount, type=t_type, category=category)
            messages.success(request, _("Transaction saved!"))
        return redirect('home')


class LoginView(TemplateView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('admin_panel' if request.user.is_superuser else 'home')
        return super().get(request, *args, **kwargs)

    def post(self, request):
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('admin_panel') if user.is_superuser else redirect('home')
        messages.error(request, _("Invalid email or password!"))
        return render(request, self.template_name)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class AdminDashboardView(TemplateView):
    template_name = 'admin_custom.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_users': User.objects.filter(is_superuser=False).count(),
            'users_list': User.objects.filter(is_superuser=False).prefetch_related('account_set'),
            'recent_transactions': Transaction.objects.all().order_by('-date')[:10],
        })
        return context


class AdminManageModelView(TemplateView):
    template_name = 'admin_model_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model_name = self.kwargs.get('model_name')
        maps = {
            'accounts': (Account, [_('User'), _('Name'), _('Balance'), _('Currency')]),
            'transactions': (Transaction, [_('Account'), _('Amount'), _('Type'), _('Category')]),
            'currencies': (Currency, [_('Name'), _('Code'), _('Rate')]),
            'goals': (FinancialGoal, [_('User'), _('Title'), _('Target'), _('Current')])
        }
        model_info = maps.get(model_name)
        if not model_info:
            return redirect('admin_panel')
        model, cols = model_info
        context.update({
            'data': model.objects.all(),
            'model_name': model_name.capitalize(),
            'columns': cols
        })
        return context


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.filter(account__user=self.request.user)
        t_type = self.request.query_params.get('type')
        if t_type: qs = qs.filter(type=t_type)
        return qs.order_by('-date')


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)