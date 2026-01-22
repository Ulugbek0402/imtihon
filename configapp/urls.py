from rest_framework import serializers
from .models import User, Account, Transaction, FinancialGoal, Currency


class CurrencySerializer(serializers.ModelSerializer):

    class Meta:
        model = Currency
        fields = ['id', 'code', 'rate']


class AccountSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'name', 'type', 'balance', 'currency', 'currency_code']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'account', 'account_name', 'amount', 'type', 'category', 'date']
        read_only_fields = ['date']


class GoalSerializer(serializers.ModelSerializer):
    progress_percent = serializers.IntegerField(source='get_progress_percent', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = FinancialGoal
        fields = ['id', 'title', 'target_amount', 'current_amount', 'currency', 'currency_code', 'progress_percent']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)