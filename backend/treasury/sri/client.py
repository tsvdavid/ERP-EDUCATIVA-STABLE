import requests
from django.conf import settings
import base64
import xml.etree.ElementTree as ET
from .xml_debug import validar_integridad_xml

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
        self.environment = int(environment)
        self.urls = urls or {}
        
        if self.environment == 2:
            self.url_recepcion = self.urls.get('reception_prod') or self.URL_RECEPCION_PROD
            self.url_autorizacion = self.urls.get('authorization_prod') or self.URL_AUTORIZACION_PROD
        else:
            self.url_recepcion = self.urls.get('reception_test') or self.URL_RECEPCION_TEST
            self.url_autorizacion = self.urls.get('authorization_test') or self.URL_AUTORIZACION_TEST

    def _parse_messages(self, element):
        """
        Helper para extraer mensajes de error/info del XML del SRI.
        """
        messages = []
        # El SRI usa una estructura <mensajes><mensaje><identificador>...</mensaje></mensajes>
        for msg_node in element.findall('.//mensaje'):
            identificador = msg_node.findtext('identificador')
            mensaje = msg_node.findtext('mensaje')
            info_adicional = msg_node.findtext('informacionAdicional')
            tipo = msg_node.findtext('tipo')
            messages.append({
                'code': identificador,
                'message': mensaje,
                'additional_info': info_adicional,
                'type': tipo
            })
        return messages

    def send_receipt(self, signed_xml_str):
        with open("TRACE_3_XML_ENVIADO.xml", "wb") as f:
            f.write(signed_xml_str.encode("utf-8"))
        
        validar_integridad_xml()

        xml_b64 = base64.b64encode(signed_xml_str.encode('utf-8')).decode('utf-8')
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
        
        for attempt in range(2):
          try:
            response = requests.post(self.url_recepcion, data=soap_env, headers=headers, timeout=30)
            root = ET.fromstring(response.text)
            
            # Namespace management (SRI responses sometimes use namespaces)
            # We look for the status tag anywhere
            estado_node = root.find('.//estado')
            if estado_node is not None:
                estado = estado_node.text
                if estado == 'RECIBIDA':
                    return True, "Comprobante Recibido", "RECIBIDA", []
                else:
                    # Extraer mensajes detallados
                    messages = self._parse_messages(root)
                    error_msg = messages[0]['message'] if messages else "Comprobante Devuelto por SRI"
                    return False, error_msg, estado, messages
            
            return False, f"Error HTTP {response.status_code}", "ERROR", []
                
          except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt == 0:
                import time; time.sleep(2)
                continue
            return False, f"Error de conexión: {str(e)}", "OFFLINE", []
          except Exception as e:
            return False, f"Error de conexión: {str(e)}", "OFFLINE", []

    def request_authorization(self, access_key):
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
            response = requests.post(self.url_autorizacion, data=soap_env, headers=headers, timeout=30)
            root = ET.fromstring(response.text)
            
            estado_node = root.find('.//estado')
            if estado_node is not None:
                estado = estado_node.text
                messages = self._parse_messages(root)
                msg_summary = messages[0]['message'] if messages else estado
                
                if estado == 'AUTORIZADO':
                    return True, "Autorizado", "AUTORIZADO", messages
                elif estado == 'EN PROCESO':
                    return False, "En Proceso", "PENDIENTE", messages
                else:
                    return False, msg_summary, "RECHAZADO", messages
            
            return False, f"Respuesta desconocida ({response.status_code})", "ERROR", []

        except Exception as e:
            return False, f"Error conexión Autorización: {e}", "OFFLINE", []
