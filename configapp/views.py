from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from decimal import Decimal
import random

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Account, Transaction, FinancialGoal, Currency, ResetCode, RecurringTransaction, Budget
from .serializers import AccountSerializer, TransactionSerializer, GoalSerializer

User = get_user_model()


def is_admin(user):
    return user.is_superuser


@extend_schema_view(
    list=extend_schema(
        summary="Barcha hisoblarni olish",
        description="Foydalanuvchining barcha moliyaviy hisoblarini ro'yxatini qaytaradi",
        tags=['Accounts']
    ),
    create=extend_schema(
        summary="Yangi hisob yaratish",
        description="Yangi moliyaviy hisob qo'shish (naqd pul yoki karta)",
        tags=['Accounts']
    ),
    retrieve=extend_schema(
        summary="Bitta hisobni olish",
        tags=['Accounts']
    ),
    update=extend_schema(
        summary="Hisobni yangilash",
        tags=['Accounts']
    ),
    partial_update=extend_schema(
        summary="Hisobni qisman yangilash",
        tags=['Accounts']
    ),
    destroy=extend_schema(
        summary="Hisobni o'chirish",
        tags=['Accounts']
    ),
)
class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Barcha tranzaksiyalarni olish",
        description="Foydalanuvchining barcha daromad va xarajat tranzaksiyalarini ro'yxatini qaytaradi",
        tags=['Transactions'],
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Tranzaksiya turi (INCOME yoki EXPENSE)',
                enum=['INCOME', 'EXPENSE']
            ),
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Kategoriya bo\'yicha filter'
            ),
        ]
    ),
    create=extend_schema(
        summary="Yangi tranzaksiya yaratish",
        description="Yangi daromad yoki xarajat qo'shish",
        tags=['Transactions']
    ),
    retrieve=extend_schema(
        summary="Bitta tranzaksiyani olish",
        tags=['Transactions']
    ),
    update=extend_schema(
        summary="Tranzaksiyani yangilash",
        tags=['Transactions']
    ),
    partial_update=extend_schema(
        summary="Tranzaksiyani qisman yangilash",
        tags=['Transactions']
    ),
    destroy=extend_schema(
        summary="Tranzaksiyani o'chirish",
        tags=['Transactions']
    ),
)
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        queryset = Transaction.objects.filter(account__user=self.request.user)

        transaction_type = self.request.query_params.get('type', None)
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)

        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__icontains=category)

        return queryset.order_by('-date')


@extend_schema_view(
    list=extend_schema(
        summary="Barcha maqsadlarni olish",
        description="Foydalanuvchining barcha moliyaviy maqsadlarini ro'yxatini qaytaradi",
        tags=['Goals']
    ),
    create=extend_schema(
        summary="Yangi maqsad yaratish",
        description="Yangi moliyaviy maqsad belgilash",
        tags=['Goals']
    ),
    retrieve=extend_schema(
        summary="Bitta maqsadni olish",
        tags=['Goals']
    ),
    update=extend_schema(
        summary="Maqsadni yangilash",
        tags=['Goals']
    ),
    partial_update=extend_schema(
        summary="Maqsadni qisman yangilash",
        tags=['Goals']
    ),
    destroy=extend_schema(
        summary="Maqsadni o'chirish",
        tags=['Goals']
    ),
)
class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)