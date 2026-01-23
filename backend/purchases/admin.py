from django.contrib import admin
from .models import Supplier, PurchaseInvoice, PurchaseItem, Withholding

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('tax_id', 'legal_name', 'trade_name', 'email', 'is_active')
    search_fields = ('tax_id', 'legal_name', 'trade_name')
    list_filter = ('is_active', 'is_special_taxpayer', 'institution')

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'supplier', 'issue_date', 'total', 'status', 'institution')
    list_filter = ('status', 'institution', 'issue_date')
    search_fields = ('document_number', 'supplier__legal_name', 'supplier__tax_id')
    inlines = [PurchaseItemInline]

@admin.register(Withholding)
class WithholdingAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'get_supplier', 'issue_date', 'ret_renta_value', 'ret_iva_value', 'sri_status')
    
    def get_supplier(self, obj):
        return obj.purchase_invoice.supplier.legal_name
    get_supplier.short_description = 'Proveedor'
