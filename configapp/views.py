from django.shortcuts import render
from .models import Account, Currency


def dashboard(request):
    user_accounts = Account.objects.filter(user=request.user)
    selected_code = request.GET.get('currency', 'UZS')
    target_currency = Currency.objects.get(code=selected_code)

    total_balance = 0
    for acc in user_accounts:
        in_base = acc.balance * acc.currency.rate
        converted = in_base / target_currency.rate
        total_balance += converted

    return render(request, 'dashboard.html', {
        'accounts': user_accounts,
        'total': total_balance,
        'currency': target_currency
    })