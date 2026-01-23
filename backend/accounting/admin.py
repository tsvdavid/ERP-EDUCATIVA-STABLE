from django.contrib import admin
from .models import Account, FiscalYear, JournalEntry, JournalItem, AccountingConfig

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'level', 'institution')
    list_filter = ('institution', 'account_type', 'level')
    search_fields = ('code', 'name')

@admin.register(AccountingConfig)
class AccountingConfigAdmin(admin.ModelAdmin):
    list_display = ('institution', 'key', 'account')
    list_filter = ('institution',)

class JournalItemInline(admin.TabularInline):
    model = JournalItem
    extra = 0

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'reference', 'state', 'total_debit', 'total_credit', 'institution')
    list_filter = ('institution', 'state', 'date')
    inlines = [JournalItemInline]
