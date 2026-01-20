from rest_framework import serializers
from .models import User, Account, Transaction, FinancialGoal, Currency

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username']

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'rate']

class AccountSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'name', 'type', 'balance', 'currency', 'currency_code']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'amount', 'type', 'category', 'date']

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialGoal
        fields = ['id', 'title', 'target_amount', 'current_amount', 'currency']