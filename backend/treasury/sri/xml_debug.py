def validar_integridad_xml():
    try:
        with open("TRACE_2_XML_FIRMADO.xml","rb") as f1, open("TRACE_3_XML_ENVIADO.xml","rb") as f2:
            if f1.read() != f2.read():
                raise Exception("XML MODIFICADO DESPUES DE FIRMAR")
            else:
                print("XML OK - SIN CAMBIOS")
    except FileNotFoundError:
        print("Archivos de traza no encontrados para validación.")
