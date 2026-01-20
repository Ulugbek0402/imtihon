from django.contrib import admin
from .models import User, Currency, Account, Transaction, RecurringTransaction, FinancialGoal

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'rate')
    list_editable = ('rate',)

admin.site.register(User)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(RecurringTransaction)
admin.site.register(FinancialGoal)