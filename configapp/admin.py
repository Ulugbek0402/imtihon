from django.contrib import admin
from .models import User, Currency, Account, Transaction, Budget, FinancialGoal, RecurringTransaction, ResetCode

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'rate')
    list_editable = ('rate',)
    search_fields = ('code',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'account', 'amount', 'type', 'category', 'date')
    list_filter = ('account__user', 'type', 'date')
    search_fields = ('category', 'account__user__email', 'account__name')

    def get_user(self, obj):
        return obj.account.user.email
    get_user.short_description = 'User'

admin.site.register(User)
admin.site.register(Account)
admin.site.register(Budget)
admin.site.register(FinancialGoal)
admin.site.register(RecurringTransaction)
admin.site.register(ResetCode)