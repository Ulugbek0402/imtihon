from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from decimal import Decimal
import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction, Budget
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer

User = get_user_model()


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
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
                category=f"Auto: {item.category}"
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


class AddAccountView(LoginRequiredMixin, View):
    def post(self, request):
        Account.objects.create(
            user=request.user, name=request.POST.get('name'),
            balance=Decimal(request.POST.get('balance', '0')),
            currency=get_object_or_404(Currency, id=request.POST.get('currency'))
        )
        messages.success(request, "Hisob qo'shildi!")
        return redirect('home')

class AddBudgetView(LoginRequiredMixin, View):
    def post(self, request):
        Budget.objects.create(
            user=request.user, name=request.POST.get('name'),
            category=request.POST.get('category'),
            amount_limit=Decimal(request.POST.get('limit', '0')),
            currency=get_object_or_404(Currency, id=request.POST.get('currency'))
        )
        messages.success(request, "Byudjet belgilandi!")
        return redirect('home')

class AddGoalView(LoginRequiredMixin, View):
    def post(self, request):
        FinancialGoal.objects.create(
            user=request.user, title=request.POST.get('title'),
            target_amount=Decimal(request.POST.get('target', '0')),
            currency=get_object_or_404(Currency, id=request.POST.get('currency'))
        )
        return redirect('home')


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin_custom.html'
    def test_func(self): return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_users': User.objects.filter(is_superuser=False).count(),
            'users_list': User.objects.filter(is_superuser=False).prefetch_related('account_set'),
            'recent_transactions': Transaction.objects.all().order_by('-date')[:10],
        })
        return context

class DeleteUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_superuser
    def post(self, request, user_id):
        User.objects.filter(id=user_id, is_superuser=False).delete()
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