import datetime
import random
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from django.utils import timezone
import xml.dom.minidom

class InvoiceXmlBuilder:
    def __init__(self, invoice):
        self.invoice = invoice
        self.institution = invoice.institution

    def compute_access_key(self):
        """
        Genera la Clave de Acceso de 49 dígitos.
        Formato: ddmmaaaattrocacsuuunnnnnnnnd
        """
        # 1. Fecha de Emisión (ddmmaaaa)
        issue_date = self.invoice.issue_date.strftime('%d%m%Y')
        
        # 2. Tipo de Comprobante (01 = Factura)
        doc_type = '01'
        
        # 3. RUC (13 dígitos)
        ruc = self.institution.ruc
        if not ruc or len(ruc) != 13:
            raise ValueError("RUC de institución inválido")

        # 4. Tipo de Ambiente (1 o 2)
        env = str(self.institution.sri_environment)
        
        # 5. Serie (Establecimiento + Punto Emisión) (3 + 3 = 6 dígitos)
        # El número de factura viene como 001-001-000000001
        parts = self.invoice.number.split('-')
        if len(parts) != 3:
             # Fallback si no tiene formato completo
             establishment = self.institution.establishment_code
             point = self.institution.emission_point
             seq = self.invoice.number.zfill(9) # Si solo guardamos el secuencial
        else:
             establishment = parts[0]
             point = parts[1]
             seq = parts[2]

        serie = f"{establishment}{point}"

        # 6. Número Secuencial (9 dígitos)
        # seq ya calculado arriba

        # 7. Código Numérico (8 dígitos) - Puede ser aleatorio o fijo
        # Usaremos el ID de la factura con padding o random si no hay ID (draft)
        # Ojo: SRI dice que debe ser numérico.
        numeric_code = str(random.randint(10000000, 99999999)) 
        
        # 8. Tipo de Emisión (1 = Normal)
        emission_type = '1'

        # Construir clave previa (48 dígitos)
        pre_key = f"{issue_date}{doc_type}{ruc}{env}{serie}{seq}{numeric_code}{emission_type}"
        
        # 9. Dígito Verificador (Módulo 11)
        check_digit = self._compute_mod11(pre_key)
        
        access_key = f"{pre_key}{check_digit}"
        return access_key

    def _compute_mod11(self, key):
        """
        Algoritmo Módulo 11 para obtener dígito verificador.
        """
        raw_key = key[::-1] # Invertir la cadena
        total = 0
        factor = 2
        
        for char in raw_key:
            total += int(char) * factor
            factor += 1
            if factor > 7:
                factor = 2
        
        remainder = total % 11
        check_digit = 11 - remainder
        
        if check_digit == 11:
            return 0
        if check_digit == 10:
            return 1
            
        return check_digit

    def build_xml(self):
        """
        Construye el XML de la factura según esquema offline v2.1.0/1.0.0
        """
        access_key = self.compute_access_key()
        
        factura = Element('factura')
        factura.set('id', 'comprobante')
        factura.set('version', '1.0.0') # Versión esquema

        # <infoTributaria>
        info_tributaria = SubElement(factura, 'infoTributaria')
        SubElement(info_tributaria, 'ambiente').text = str(self.institution.sri_environment)
        SubElement(info_tributaria, 'tipoEmision').text = '1'
        SubElement(info_tributaria, 'razonSocial').text = self.institution.name
        SubElement(info_tributaria, 'nombreComercial').text = self.institution.name # A veces difiere, usar nombre por defecto
        SubElement(info_tributaria, 'ruc').text = self.institution.ruc
        SubElement(info_tributaria, 'claveAcceso').text = access_key
        SubElement(info_tributaria, 'codDoc').text = '01' # Factura
        
        # Serie split
        parts = self.invoice.number.split('-')
        est = parts[0] if len(parts)==3 else self.institution.establishment_code
        pto = parts[1] if len(parts)==3 else self.institution.emission_point
        seq = parts[2] if len(parts)==3 else self.invoice.number.zfill(9)

        SubElement(info_tributaria, 'estab').text = est
        SubElement(info_tributaria, 'ptoEmi').text = pto
        SubElement(info_tributaria, 'secuencial').text = seq
        SubElement(info_tributaria, 'dirMatriz').text = self.institution.address or 'Sin Dirección'
        # Agente de retención? Contribuyente especial?
        if self.institution.special_taxpayer_number:
            SubElement(info_tributaria, 'contribuyenteEspecial').text = self.institution.special_taxpayer_number
        
        # <infoFactura>
        info_factura = SubElement(factura, 'infoFactura')
        SubElement(info_factura, 'fechaEmision').text = self.invoice.issue_date.strftime('%d/%m/%Y')
        SubElement(info_factura, 'dirEstablecimiento').text = self.institution.address or 'Sin Dirección'
        if self.institution.obligado_contabilidad:
             SubElement(info_factura, 'obligadoContabilidad').text = 'SI'
        else:
             SubElement(info_factura, 'obligadoContabilidad').text = 'NO'
        
        # Tipo ID Comprador (04: RUC, 05: Cedula, 06: Pasaporte, 07: Final)
        # Lógica simplificada:
        client_id_type = '05' # Cédula por defecto
        if self.invoice.client_ruc == '9999999999999':
             client_id_type = '07'
        elif len(self.invoice.client_ruc) == 13:
             client_id_type = '04'
        
        SubElement(info_factura, 'tipoIdentificacionComprador').text = client_id_type
        SubElement(info_factura, 'razonSocialComprador').text = self.invoice.client_name
        SubElement(info_factura, 'identificacionComprador').text = self.invoice.client_ruc
        SubElement(info_factura, 'direccionComprador').text = self.invoice.client_address or 'Sin Dirección'
        
        # Totales
        SubElement(info_factura, 'totalSinImpuestos').text = f"{self.invoice.total - self.invoice.iva_total:.2f}"
        SubElement(info_factura, 'totalDescuento').text = f"{self.invoice.discount:.2f}"
        
        # Total con impuestos breakdown
        total_con_imp = SubElement(info_factura, 'totalConImpuestos')
        
        # IVA 0
        if self.invoice.subtotal_0 > 0:
            imp0 = SubElement(total_con_imp, 'totalImpuesto')
            SubElement(imp0, 'codigo').text = '2' # IVA
            SubElement(imp0, 'codigoPorcentaje').text = '0' # 0%
            SubElement(imp0, 'baseImponible').text = f"{self.invoice.subtotal_0:.2f}"
            SubElement(imp0, 'valor').text = '0.00'

        # IVA 15 (Codigo 4)
        if self.invoice.subtotal_15 > 0:
            imp15 = SubElement(total_con_imp, 'totalImpuesto')
            SubElement(imp15, 'codigo').text = '2' # IVA
            SubElement(imp15, 'codigoPorcentaje').text = '4' # 15% (Verificar tabla 17 SRI, a veces es 2, 3...)
            # SRI Code 4 = 15% (Updated recently, check standard - previously 2=12%, 3=14%)
            # Assuming '4' for 15% as per recent Ecuador updates.
            SubElement(imp15, 'baseImponible').text = f"{self.invoice.subtotal_15:.2f}"
            SubElement(imp15, 'valor').text = f"{self.invoice.iva_total:.2f}"

        SubElement(info_factura, 'propina').text = '0.00'
        SubElement(info_factura, 'importeTotal').text = f"{self.invoice.total:.2f}"
        SubElement(info_factura, 'moneda').text = 'DOLAR'
        
        # Pagos
        pagos = SubElement(info_factura, 'pagos')
        pago = SubElement(pagos, 'pago')
        # Metodo Pago SRI code?
        pay_code = '01' # Sin utilización sistema financiero
        if self.invoice.payment_method and hasattr(self.invoice.payment_method, 'code'):
             pay_code = self.invoice.payment_method.code
        
        SubElement(pago, 'formaPago').text = pay_code
        SubElement(pago, 'total').text = f"{self.invoice.total:.2f}"
        SubElement(pago, 'plazo').text = '0'
        SubElement(pago, 'unidadTiempo').text = 'dias'

        # <detalles>
        detalles = SubElement(factura, 'detalles')
        for det in self.invoice.details.all():
            detalle = SubElement(detalles, 'detalle')
            SubElement(detalle, 'codigoPrincipal').text = str(det.concept.id)
            SubElement(detalle, 'descripcion').text = det.concept.name
            SubElement(detalle, 'cantidad').text = f"{det.quantity:.2f}" # SRI pide hasta x decimales, 2 ok
            SubElement(detalle, 'precioUnitario').text = f"{det.unit_price:.2f}"
            SubElement(detalle, 'descuento').text = '0.00'
            SubElement(detalle, 'precioTotalSinImpuesto').text = f"{det.subtotal:.2f}"
            
            impuestos = SubElement(detalle, 'impuestos')
            impuesto = SubElement(impuestos, 'impuesto')
            SubElement(impuesto, 'codigo').text = '2' # IVA
            
            # Rate determination
            if det.concept.iva_rate > 0:
                 SubElement(impuesto, 'codigoPorcentaje').text = '4' # 15%
                 SubElement(impuesto, 'tarifa').text = '15.00'
                 val_iva = det.subtotal * Decimal('0.15')
            else:
                 SubElement(impuesto, 'codigoPorcentaje').text = '0' # 0%
                 SubElement(impuesto, 'tarifa').text = '0.00'
                 val_iva = Decimal('0.00')

            SubElement(impuesto, 'baseImponible').text = f"{det.subtotal:.2f}"
            SubElement(impuesto, 'valor').text = f"{val_iva:.2f}"

        # <infoAdicional> si email existe
        if self.invoice.client_email:
            info_adicional = SubElement(factura, 'infoAdicional')
            campo_email = SubElement(info_adicional, 'campoAdicional')
            campo_email.set('nombre', 'Email')
            campo_email.text = self.invoice.client_email

        # Pretty Print
        rough_string = tostring(factura, 'utf-8')
        reparsed = xml.dom.minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="  ")
        
        # Remove XML header if needed or keep encoding
        return access_key, xml_str
