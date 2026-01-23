import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from django.db.models import Sum
from treasury.models import Invoice
from purchases.models import PurchaseInvoice
from .constants import *

class ATSGenerator:
    def __init__(self, institution, year, month):
        self.institution = institution
        self.year = year
        self.month = month
        self.start_date = date(year, month, 1)
        # Calculate end date rough approx or use calendar
        if month == 12:
            self.end_date = date(year + 1, 1, 1)
        else:
            self.end_date = date(year, month + 1, 1)

    def generate_xml(self):
        root = ET.Element("iva")
        
        # 1. Header
        self._add_header(root)
        
        # 2. Compras
        self._add_compras(root)
        
        # 3. Ventas
        self._add_ventas(root)
        
        # 4. Anulados (Optional/TODO)
        
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    def _add_header(self, root):
        ET.SubElement(root, "TipoIDInformante").text = "R" # RUC
        ET.SubElement(root, "IdInformante").text = self.institution.ruc
        ET.SubElement(root, "razonSocial").text = self.institution.name
        ET.SubElement(root, "Anio").text = str(self.year)
        ET.SubElement(root, "Mes").text = f"{self.month:02d}"
        ET.SubElement(root, "numEstabRuc").text = self.institution.establishment_code.lstrip('0') or '1' # Typically '001' -> 1
        ET.SubElement(root, "totalVentas").text = f"{self._get_total_ventas():.2f}"
        ET.SubElement(root, "codigoOperativo").text = "IVA"

    def _get_total_ventas(self):
        ventas = Invoice.objects.filter(
            institution=self.institution,
            issue_date__gte=self.start_date,
            issue_date__lt=self.end_date,
            status__in=['ISSUED', 'AUTHORIZED', 'SENT'] # Include recently sent
        ).aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
        return ventas

    def _add_compras(self, root):
        compras = ET.SubElement(root, "compras")
        
        invoices = PurchaseInvoice.objects.filter(
            institution=self.institution,
            issue_date__gte=self.start_date,
            issue_date__lt=self.end_date,
            status='VALIDATED'
        ).select_related('supplier', 'withholding')

        for inv in invoices:
            det = ET.SubElement(compras, "detalleCompras")
            ET.SubElement(det, "codSustento").text = inv.sustento_tributario
            ET.SubElement(det, "tpIdProv").text = TP_ID_RUC if inv.supplier.tax_id_type == 'RUC' else TP_ID_CEDULA
            ET.SubElement(det, "idProv").text = inv.supplier.tax_id
            ET.SubElement(det, "tipoComprobante").text = COMPROBANTE_FACTURA 
            ET.SubElement(det, "tipoProv").text = PROVEEDOR_RESIDENTE
            ET.SubElement(det, "denoProv").text = inv.supplier.legal_name
            
            # Auth
            ET.SubElement(det, "parteRel").text = PARTE_RELACIONADA_NO
            ET.SubElement(det, "fechaRegistro").text = inv.registration_date.strftime("%d/%m/%Y")
            ET.SubElement(det, "establecimiento").text = inv.document_number[:3]
            ET.SubElement(det, "puntoEmision").text = inv.document_number[4:7]
            ET.SubElement(det, "secuencial").text = inv.document_number[8:]
            ET.SubElement(det, "fechaEmision").text = inv.issue_date.strftime("%d/%m/%Y")
            ET.SubElement(det, "autorizacion").text = inv.authorization_code or "9999999999" 

            # Values
            ET.SubElement(det, "baseNoGravaIva").text = f"{inv.subtotal_no_obj:.2f}"
            ET.SubElement(det, "baseImponible").text = f"{inv.subtotal_0:.2f}" 
            ET.SubElement(det, "baseImpGrav").text = f"{inv.subtotal_15:.2f}" 
            ET.SubElement(det, "baseImpExe").text = "0.00"
            ET.SubElement(det, "montoIce").text = "0.00"
            ET.SubElement(det, "montoIva").text = f"{inv.iva:.2f}"
            
            # Retentions (If Withholding exists)
            # select_related populates withholding with None if missing, so hasattr is True but value is None
            withholding = getattr(inv, 'withholding', None)
            val_ret_iva = withholding.ret_iva_value if withholding else 0
            val_ret_renta = withholding.ret_renta_value if withholding else 0
            
            ET.SubElement(det, "valRetBien10").text = "0.00" 
            ET.SubElement(det, "valRetServ20").text = "0.00"
            ET.SubElement(det, "valorRetIva").text = f"{val_ret_iva:.2f}"
            ET.SubElement(det, "valorRetRenta").text = f"{val_ret_renta:.2f}"
            
            # Payment
            pago = ET.SubElement(det, "formasDePago")
            ET.SubElement(pago, "formaPago").text = inv.payment_method

    def _add_ventas(self, root):
        ventas_elem = ET.SubElement(root, "ventas")
        
        invoices = Invoice.objects.filter(
            institution=self.institution,
            issue_date__gte=self.start_date,
            issue_date__lt=self.end_date,
            status__in=['ISSUED', 'AUTHORIZED', 'SENT']
        ).select_related('payment_method').iterator()

        for inv in invoices:
            det = ET.SubElement(ventas_elem, "detalleVentas")
            ET.SubElement(det, "tpIdCliente").text = TP_ID_CLIENTE_CEDULA if len(inv.client_ruc) == 10 else TP_ID_CLIENTE_RUC 
            ET.SubElement(det, "idCliente").text = inv.client_ruc
            ET.SubElement(det, "parteRelVtas").text = PARTE_RELACIONADA_NO
            
            ET.SubElement(det, "tipoComprobante").text = COMPROBANTE_VENTA_FACTURA 
            ET.SubElement(det, "tipoEmision").text = "F" 
            ET.SubElement(det, "numeroComprobantes").text = "1"
            ET.SubElement(det, "baseNoGravaIva").text = f"{inv.subtotal_0:.2f}" 
            ET.SubElement(det, "baseImponible").text = "0.00" 
            ET.SubElement(det, "baseImpGrav").text = f"{inv.subtotal_15:.2f}"
            ET.SubElement(det, "montoIva").text = f"{inv.iva_total:.2f}"
            ET.SubElement(det, "montoIce").text = "0.00"
            ET.SubElement(det, "valorRetIva").text = "0.00"
            ET.SubElement(det, "valorRetRenta").text = "0.00"
            
            # Formas de Pago
            pagos = ET.SubElement(det, "formasDePago")
            ET.SubElement(pagos, "formaPago").text = PAGO_OTROS_SISTEMA_FINANCIERO
