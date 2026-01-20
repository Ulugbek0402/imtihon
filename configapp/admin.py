from django.contrib import admin
from .models import User, Currency, Account, Transaction, Budget, FinancialGoal, RecurringTransaction, ResetCode


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'rate')

    list_editable = ('rate',)

    search_fields = ('code',)


admin.site.register(User)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(FinancialGoal)
admin.site.register(RecurringTransaction)
admin.site.register(ResetCode)