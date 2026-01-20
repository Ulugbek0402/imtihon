from django.shortcuts import render
from django.db.models import Sum
from .models import Account, Currency, Transaction, FinancialGoal


def dashboard(request):
    selected_code = request.GET.get('currency', 'UZS')
    target_currency = Currency.objects.get(code=selected_code)
    accounts = Account.objects.filter(user=request.user)
    goals = FinancialGoal.objects.filter(user=request.user)

    total_balance = 0
    for acc in accounts:
        balance_in_base = acc.balance * acc.currency.rate
        converted = balance_in_base / target_currency.rate
        total_balance += converted

    expenses = Transaction.objects.filter(
        account__user=request.user,
        type='EXPENSE'
    ).values('category').annotate(total=Sum('amount'))

    chart_labels = [item['category'] for item in expenses]
    chart_data = [float(item['total']) for item in expenses]

    return render(request, 'dashboard.html', {
        'accounts': accounts,
        'goals': goals,
        'total': total_balance,
        'selected_currency': target_currency,
        'all_currencies': Currency.objects.all(),
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })