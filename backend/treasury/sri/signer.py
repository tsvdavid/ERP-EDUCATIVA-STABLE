import base64
import hashlib
import uuid
import copy
from datetime import datetime, timezone, timedelta
from lxml import etree
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

C14N_ALGO = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"

class XadesSigner:
    """
    Firma XMLs usando formato XAdES-BES estricto requerido por el SRI Ecuador.
    Versión final optimizada para máxima compatibilidad y corrección de Error 39.
    """
    def __init__(self, p12_path, password):
        self.p12_path = p12_path
        self.password = password
        self._load_key_cert()

    def _load_key_cert(self):
        try:
            with open(self.p12_path, 'rb') as f:
                p12_data = f.read()
            
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                p12_data, 
                self.password.encode() if self.password else None
            )
            
            self.private_key = private_key
            self.certificate = certificate
            self.cert_der = certificate.public_bytes(serialization.Encoding.DER)
            self.cert_b64 = base64.b64encode(self.cert_der).decode()
        except Exception as e:
            raise ValueError(f"Error cargando firma electrónica: {e}")

    def sign_xml(self, xml_string):
        parser = etree.XMLParser(remove_blank_text=True)
        
        # Namespaces y Algoritmos
        ns_ds = "http://www.w3.org/2000/09/xmldsig#"
        ns_xades = "http://uri.etsi.org/01903/v1.3.2#"
        
        uid = str(uuid.uuid4())
        signature_id = f"xmldsig-{uid}"
        props_id = f"{signature_id}-signedprops"
        ref0_id = f"{signature_id}-ref0"
        object_id = f"{signature_id}-object"
        
        # Iniciar raíz del documento
        root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)

        # ==========================================
        # 1. DIGEST DEL DOCUMENTO (CLONADO Y LIMPIO)
        # ==========================================
        root_for_digest = copy.deepcopy(root)
        for sig in root_for_digest.findall(".//ds:Signature", namespaces={"ds": ns_ds}):
            sig.getparent().remove(sig)
            
        doc_c14n = etree.tostring(
            root_for_digest,
            method="c14n",
            exclusive=False,
            with_comments=False
        )
        doc_digest = base64.b64encode(hashlib.sha1(doc_c14n).digest()).decode()
        
        # ==========================================
        # 2. ARMAR ESTRUCTURA COMPLETA PRIMERO
        #    (para que SignedProperties herede los
        #     namespaces correctos del árbol)
        # ==========================================
        
        # A) Crear Signature → Object → QualifyingProperties → SignedProperties
        signature = etree.SubElement(root, f"{{{ns_ds}}}Signature", nsmap={"ds": ns_ds}, Id=signature_id)
        
        # Placeholder para SignedInfo (se llenará después)
        signed_info = etree.SubElement(signature, f"{{{ns_ds}}}SignedInfo")
        etree.SubElement(signed_info, f"{{{ns_ds}}}CanonicalizationMethod", Algorithm=C14N_ALGO)
        etree.SubElement(signed_info, f"{{{ns_ds}}}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        
        # Placeholder SignatureValue
        sig_value_node = etree.SubElement(signature, f"{{{ns_ds}}}SignatureValue")
        
        # KeyInfo
        key_info_node = etree.SubElement(signature, f"{{{ns_ds}}}KeyInfo")
        x509_data = etree.SubElement(key_info_node, f"{{{ns_ds}}}X509Data")
        etree.SubElement(x509_data, f"{{{ns_ds}}}X509Certificate").text = self.cert_b64
        
        # Object → QualifyingProperties → SignedProperties
        obj = etree.SubElement(signature, f"{{{ns_ds}}}Object", Id=object_id)
        qualifying = etree.SubElement(obj, f"{{{ns_xades}}}QualifyingProperties", nsmap={"xades": ns_xades}, Target=f"#{signature_id}")
        
        # Crear SignedProperties DENTRO del árbol (no aislado)
        signed_props = etree.SubElement(qualifying, f"{{{ns_xades}}}SignedProperties", Id=props_id)
        signed_sig_props = etree.SubElement(signed_props, f"{{{ns_xades}}}SignedSignatureProperties")
        
        ec_tz = timezone(timedelta(hours=-5))
        etree.SubElement(signed_sig_props, f"{{{ns_xades}}}SigningTime").text = datetime.now(ec_tz).isoformat(timespec="milliseconds")
        
        signing_cert = etree.SubElement(signed_sig_props, f"{{{ns_xades}}}SigningCertificate")
        cert_node = etree.SubElement(signing_cert, f"{{{ns_xades}}}Cert")
        cert_digest = etree.SubElement(cert_node, f"{{{ns_xades}}}CertDigest")
        etree.SubElement(cert_digest, f"{{{ns_ds}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        etree.SubElement(cert_digest, f"{{{ns_ds}}}DigestValue").text = base64.b64encode(hashlib.sha1(self.cert_der).digest()).decode()
        
        issuer_serial = etree.SubElement(cert_node, f"{{{ns_xades}}}IssuerSerial")
        issuer_parts = []
        for attr in self.certificate.issuer:
            issuer_parts.append(attr.rfc4514_string())
        etree.SubElement(issuer_serial, f"{{{ns_ds}}}X509IssuerName").text = ",".join(issuer_parts)
        etree.SubElement(issuer_serial, f"{{{ns_ds}}}X509SerialNumber").text = str(self.certificate.serial_number)
        
        data_props = etree.SubElement(signed_props, f"{{{ns_xades}}}SignedDataObjectProperties")
        data_format = etree.SubElement(data_props, f"{{{ns_xades}}}DataObjectFormat", ObjectReference=f"#{ref0_id}")
        etree.SubElement(data_format, f"{{{ns_xades}}}MimeType").text = "text/xml"
        
        # ==========================================
        # 3. CALCULAR DIGEST DE SignedProperties
        #    (AHORA que ya está en el árbol con todos
        #     los namespaces heredados correctamente)
        # ==========================================
        props_c14n = etree.tostring(signed_props, method="c14n", exclusive=False, with_comments=False)
        props_digest = base64.b64encode(hashlib.sha1(props_c14n).digest()).decode()

        # ==========================================
        # 4. LLENAR SignedInfo CON LOS DIGESTS
        # ==========================================
        # [A] Reference SignedProperties (PRIMERO)
        ref_props = etree.SubElement(signed_info, f"{{{ns_ds}}}Reference", Type="http://uri.etsi.org/01903#SignedProperties", URI=f"#{props_id}")
        transforms_props = etree.SubElement(ref_props, f"{{{ns_ds}}}Transforms")
        etree.SubElement(transforms_props, f"{{{ns_ds}}}Transform", Algorithm=C14N_ALGO)
        etree.SubElement(ref_props, f"{{{ns_ds}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        etree.SubElement(ref_props, f"{{{ns_ds}}}DigestValue").text = props_digest

        # [B] Reference Documento (ÚLTIMO)
        ref_doc = etree.SubElement(signed_info, f"{{{ns_ds}}}Reference", Id=ref0_id, URI="#comprobante")
        transforms = etree.SubElement(ref_doc, f"{{{ns_ds}}}Transforms")
        etree.SubElement(transforms, f"{{{ns_ds}}}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        etree.SubElement(ref_doc, f"{{{ns_ds}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        etree.SubElement(ref_doc, f"{{{ns_ds}}}DigestValue").text = doc_digest
        
        # ==========================================
        # 5. FIRMAR SignedInfo Y COMPLETAR
        # ==========================================
        si_c14n = etree.tostring(signed_info, method="c14n", exclusive=False, with_comments=False)
        signature_bytes = self.private_key.sign(si_c14n, padding.PKCS1v15(), hashes.SHA1())
        sig_value_node.text = base64.b64encode(signature_bytes).decode()
        
        xml_firmado = etree.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')

        with open("TRACE_2_XML_FIRMADO.xml", "wb") as f:
            f.write(xml_firmado.encode("utf-8"))

        if "xml-exc-c14n" in xml_firmado:
            raise Exception("xml-exc-c14n detectado")

        return xml_firmado