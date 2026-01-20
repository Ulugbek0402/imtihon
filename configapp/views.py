from django.shortcuts import render, redirect
from django.utils import timezone
from rest_framework import viewsets
from .models import User, Account, Transaction, FinancialGoal, Currency
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer


def dashboard(request):
    selected_code = request.GET.get('currency', 'UZS')
    target_currency = Currency.objects.get(code=selected_code)
    accounts = Account.objects.filter(user=request.user)

    total_balance = 0
    for acc in accounts:
        balance_in_base = acc.balance * acc.currency.rate
        converted = balance_in_base / target_currency.rate
        total_balance += converted

    return render(request, 'dashboard.html', {
        'accounts': accounts,
        'total': total_balance,
        'selected_currency': target_currency,
        'all_currencies': Currency.objects.all()
    })


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