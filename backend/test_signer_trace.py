import os
import sys

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from treasury.sri.signer import XadesSigner
from treasury.sri.client import SriClient

def run_test():
    p12_path = "/app/media/institutions/signatures/HENRY_EDISON_VALENCIA_PUENTE_1714578273-230126013301.p12"
    password = "Hevp102014"
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<factura id="comprobante" version="1.1.0">
    <infoTributaria>
        <ambiente>1</ambiente>
        <tipoEmision>1</tipoEmision>
        <razonSocial>PRUEBA</razonSocial>
        <ruc>1714578273001</ruc>
        <claveAcceso>0305202601171457827300110010010000005461234567812</claveAcceso>
        <codDoc>01</codDoc>
        <estab>001</estab>
        <ptoEmi>001</ptoEmi>
        <secuencial>000000546</secuencial>
        <dirMatriz>QUITO</dirMatriz>
    </infoTributaria>
    <infoFactura>
        <fechaEmision>03/05/2026</fechaEmision>
        <dirEstablecimiento>QUITO</dirEstablecimiento>
        <obligadoContabilidad>NO</obligadoContabilidad>
        <tipoIdentificacionComprador>05</tipoIdentificacionComprador>
        <razonSocialComprador>CLIENTE PRUEBA</razonSocialComprador>
        <identificacionComprador>1714578273</identificacionComprador>
        <totalSinImpuestos>10.00</totalSinImpuestos>
        <totalDescuento>0.00</totalDescuento>
        <totalConImpuestos>
            <totalImpuesto>
                <codigo>2</codigo>
                <codigoPorcentaje>0</codigoPorcentaje>
                <baseImponible>10.00</baseImponible>
                <valor>0.00</valor>
            </totalImpuesto>
        </totalConImpuestos>
        <propina>0.00</propina>
        <importeTotal>10.00</importeTotal>
        <moneda>DOLAR</moneda>
    </infoFactura>
    <detalles>
        <detalle>
            <codigoPrincipal>P001</codigoPrincipal>
            <descripcion>PRODUCTO PRUEBA</descripcion>
            <cantidad>1.00</cantidad>
            <precioUnitario>10.00</precioUnitario>
            <descuento>0.00</descuento>
            <precioTotalSinImpuesto>10.00</precioTotalSinImpuesto>
            <impuestos>
                <impuesto>
                    <codigo>2</codigo>
                    <codigoPorcentaje>0</codigoPorcentaje>
                    <tarifa>0</tarifa>
                    <baseImponible>10.00</baseImponible>
                    <valor>0.00</valor>
                </impuesto>
            </impuestos>
        </detalle>
    </detalles>
</factura>"""

    print("--- PASO 1: Generando TRACE_1 ---")
    with open("TRACE_1_XML_ORIGINAL.xml", "wb") as f:
        f.write(xml_content.encode("utf-8"))
        
    print("--- PASO 2: Firmando (Generando TRACE_2) ---")
    signer = XadesSigner(p12_path, password)
    signed_xml = signer.sign_xml(xml_content)
    
    print("--- PASO 3: Enviando (Generando TRACE_3 y Validando) ---")
    client = SriClient(environment=1)
    # Mocking urls if needed, but here we just care about the trace
    try:
        client.send_receipt(signed_xml)
    except Exception as e:
        print(f"Error en validación: {e}")

if __name__ == "__main__":
    run_test()
