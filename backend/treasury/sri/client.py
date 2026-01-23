import requests
from django.conf import settings
import base64

class SriClient:
    """
    Cliente para interactuar con los Web Services del SRI (Offline).
    """
    
    # URLs Ambiente de Pruebas
    URL_RECEPCION_TEST = "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline"
    URL_AUTORIZACION_TEST = "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline"
    
    # URLs Ambiente de Producción
    URL_RECEPCION_PROD = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline"
    URL_AUTORIZACION_PROD = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline"

    def __init__(self, environment, urls=None):
        """
        environment: 1 (Pruebas) o 2 (Producción)
        urls: dict with custom URLs {'recepcion_test': '...', ...}
        """
        self.environment = int(environment)
        self.urls = urls or {}
        
        if self.environment == 2:
            self.url_recepcion = self.urls.get('reception_prod') or self.URL_RECEPCION_PROD
            self.url_autorizacion = self.urls.get('authorization_prod') or self.URL_AUTORIZACION_PROD
        else:
            self.url_recepcion = self.urls.get('reception_test') or self.URL_RECEPCION_TEST
            self.url_autorizacion = self.urls.get('authorization_test') or self.URL_AUTORIZACION_TEST

    def send_receipt(self, signed_xml_str):
        """
        Envía el XML firmado al endpoint de Recepción.
        Retorna (exito: bool, mensaje: str, estado: str)
        """
        # Codificar XML a base64
        xml_b64 = base64.b64encode(signed_xml_str.encode('utf-8')).decode('utf-8')
        
        # Construir SOAP Envelope manualmente
        soap_env = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ec="http://ec.gob.sri.ws.recepcion">
           <soapenv:Header/>
           <soapenv:Body>
              <ec:validarComprobante>
                 <xml>{xml_b64}</xml>
              </ec:validarComprobante>
           </soapenv:Body>
        </soapenv:Envelope>
        """
        
        headers = {'Content-Type': 'text/xml;charset=UTF-8'}
        
        try:
            response = requests.post(self.url_recepcion, data=soap_env, headers=headers, timeout=10)
            # Analizar respuesta básica (se podría usar xmltodict o lxml para parsear mejor)
            # Respuesta esperada: <estado>RECIBIDA</estado> o <estado>DEVUELTA</estado>
            
            resp_text = response.text
            if "<estado>RECIBIDA</estado>" in resp_text:
                return True, "Comprobante Recibido", "RECIBIDA"
            elif "<estado>DEVUELTA</estado>" in resp_text:
                # Extraer mensaje error simple
                # PENDIENTE: Parsear mejor el mensaje de error
                return False, "Comprobante Devuelto por SRI", "DEVUELTA"
            else:
                return False, f"Respuesta inesperada: {response.status_code}", "ERROR"
                
        except Exception as e:
            return False, f"Error de conexión: {str(e)}", "OFFLINE"

    def request_authorization(self, access_key):
        """
        Consulta la autorización de un comprobante por Clave de Acceso.
        """
        soap_env = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ec="http://ec.gob.sri.ws.autorizacion">
           <soapenv:Header/>
           <soapenv:Body>
              <ec:autorizacionComprobante>
                 <claveAccesoComprobante>{access_key}</claveAccesoComprobante>
              </ec:autorizacionComprobante>
           </soapenv:Body>
        </soapenv:Envelope>
        """
        
        headers = {'Content-Type': 'text/xml;charset=UTF-8'}
        
        try:
            response = requests.post(self.url_autorizacion, data=soap_env, headers=headers, timeout=10)
            resp_text = response.text
            
            if "<estado>AUTORIZADO</estado>" in resp_text:
                 # Extraer fecha
                 # <fechaAutorizacion>2024-01-01T12:00:00</fechaAutorizacion>
                 # PENDIENTE: Parsear fecha
                 return True, "Autorizado", "AUTORIZADO", resp_text
            elif "<estado>NO AUTORIZADO</estado>" in resp_text:
                 return False, "No Autorizado", "RECHAZADO", resp_text
            elif "<estado>EN PROCESO</estado>" in resp_text:
                 return False, "En Proceso", "PENDIENTE", resp_text
            else:
                 return False, "Respuesta desconocida", "ERROR", resp_text

        except Exception as e:
            return False, f"Error conexión Autorización: {e}", "OFFLINE", None
