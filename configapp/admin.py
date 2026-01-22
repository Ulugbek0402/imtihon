from django.contrib import admin
from .models import (
    User, Currency, Account, Transaction,
    Budget, FinancialGoal, RecurringTransaction, ResetCode
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')

@admin.register(ResetCode)
class ResetCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'rate')
    list_editable = ('rate',)
    search_fields = ('code',)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'balance', 'currency')
    list_filter = ('currency', 'user')
    search_fields = ('name', 'user__email')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'account', 'amount', 'type', 'category', 'date')
    list_filter = ('type', 'date', 'account__user')
    search_fields = ('category', 'account__user__email', 'account__name')
    date_hierarchy = 'date'

    def get_user(self, obj):
        return obj.account.user.email
    get_user.short_description = 'User'

@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'amount', 'frequency', 'next_date')
    list_filter = ('frequency',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount_limit', 'month', 'year')
    list_filter = ('month', 'year')

@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'target_amount', 'current_amount')
    list_filter = ('currency',)