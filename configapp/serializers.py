from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from .models import User, Account, Transaction, FinancialGoal, Currency

class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            if not user:
                raise serializers.ValidationError(
                    _('Unable to log in with provided credentials.'),
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                _('Must include "email" and "password".'),
                code='authorization'
            )

        attrs['user'] = user
        return attrs

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