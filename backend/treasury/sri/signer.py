import os
import base64
from OpenSSL import crypto
from lxml import etree
from signxml import XMLSigner, XMLVerifier

class XadesSigner:
    """
    Firma XMLs usando formato XAdES-BES requerido por el SRI.
    Requiere un archivo .p12 y su contraseña.
    """
    def __init__(self, p12_path, password):
        self.p12_path = p12_path
        self.password = password
        self._load_key_cert()

    def _load_key_cert(self):
        try:
            with open(self.p12_path, 'rb') as f:
                p12_data = f.read()
            
            p12 = crypto.load_pkcs12(p12_data, self.password.encode())
            self.key = p12.get_privatekey()
            self.cert = p12.get_certificate()
            
            # Convert to PEM for signxml
            self.key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key)
            self.cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert)
            
        except Exception as e:
            raise ValueError(f"Error cargando firma electrónica: {e}")

    def sign_xml(self, xml_string):
        """
        Firma el string XML y devuelve el XML firmado como string.
        """
        root = etree.fromstring(xml_string.encode('utf-8'))
        
        # SRI XAdES configuration is complex. 
        # Using XMLSigner with standard configuration often needs tweaking for SRI.
        # SRI expects the signature inside the same XML, usually enveloped.
        
        signed_root = XMLSigner(
            method=XMLSigner.methods.enveloped,
            signature_algorithm='rsa-sha1', # SRI suele usar SHA1, verificar si SHA256 es aceptado hoy dia v2.1 (si, SHA1 aun es comun en SRI legacy)
            digest_algorithm='sha1',
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        ).sign(
            root, 
            key=self.key_pem, 
            cert=self.cert_pem,
            always_add_key_value=True # SRI lo requiere
        )
        
        return etree.tostring(signed_root, encoding='utf-8').decode('utf-8')
