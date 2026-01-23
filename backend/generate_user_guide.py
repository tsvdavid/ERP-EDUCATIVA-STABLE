
import os
import django
from django.conf import settings
from django.template import Context, Template
from xhtml2pdf import pisa
import io

# Setup Django standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def generate_pdf():
    output_filename = "Guia_Funcional_ERP_Educativa.pdf"
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {
                size: a4 portrait;
                @frame header_frame {           /* Static Frame */
                    -pdf-frame-content: header_content;
                    left: 50pt; width: 512pt; top: 50pt; height: 40pt;
                }
                @frame content_frame {          /* Content Frame */
                    left: 50pt; width: 512pt; top: 90pt; height: 632pt;
                }
                @frame footer_frame {           /* Another Static Frame */
                    -pdf-frame-content: footer_content;
                    left: 50pt; width: 512pt; top: 772pt; height: 20pt;
                }
            }
            body {
                font-family: Helvetica, sans-serif;
                font-size: 12px;
                color: #333333;
            }
            h1 {
                font-size: 24px;
                color: #1a5f7a; /* Dark Blue */
                text-align: center;
                margin-bottom: 20px;
            }
            h2 {
                font-size: 18px;
                color: #2c3e50;
                border-bottom: 1px solid #ccc;
                padding-bottom: 5px;
                margin-top: 20px;
            }
            h3 {
                font-size: 14px;
                color: #e67e22; /* Orange accent */
                margin-top: 15px;
                margin-bottom: 5px;
            }
            p {
                margin-bottom: 10px;
                line-height: 1.5;
                text-align: justify;
            }
            ul {
                margin-bottom: 15px;
            }
            li {
                margin-bottom: 5px;
            }
            .toc {
                background-color: #f9f9f9;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-bottom: 30px;
            }
            .module-block {
                margin-bottom: 25px;
            }
            .cover-page {
                text-align: center;
                padding-top: 200px;
            }
            .cover-title {
                font-size: 36px;
                font-weight: bold;
                color: #1a5f7a;
                margin-bottom: 20px;
            }
            .cover-subtitle {
                font-size: 20px;
                color: #7f8c8d;
            }
            .page-break {
                 pdf: next-page;
            }
        </style>
    </head>
    <body>
        <!-- Header & Footer -->
        <div id="header_content">
            <div style="text-align: right; color: #7f8c8d; font-size: 9px;">
                ERP EDUCATIVA - Guía Funcional
            </div>
        </div>
        <div id="footer_content">
            <div style="text-align: center; color: #7f8c8d; font-size: 9px;">
                Página <pdf:pagenumber>
            </div>
        </div>

        <!-- Cover Page -->
        <div class="cover-page">
            <div class="cover-title">ERP EDUCATIVA</div>
            <div class="cover-subtitle">Guía Funcional del Sistema</div>
            <br/><br/><br/>
            <p style="text-align: center;">Una solución integral para la gestión académica y administrativa.</p>
            <br/><br/>
            <p style="text-align: center;">Generado el: 2026-01-16</p>
        </div>
        
        <div class="page-break"></div>

        <!-- Introduction -->
        <h1>Introducción</h1>
        <p>Bienvenido al <b>ERP EDUCATIVA</b>. Este sistema ha sido diseñado para simplificar y potenciar la gestión de instituciones educativas, integrando procesos académicos, financieros y administrativos en una sola plataforma intuitiva y segura.</p>
        <p>Esta guía detalla las bondades y funcionalidades organizadas por módulos, para que usted pueda aprovechar al máximo todas las herramientas disponibles.</p>

        <!-- Module 1: Academic -->
        <div class="module-block">
            <h2>1. Módulo Académico</h2>
            <p>El corazón de la institución. Gestione todo el ciclo de vida académico de manera eficiente y centralizada.</p>
            
            <h3>Gestión de Periodos Académicos</h3>
            <ul>
                <li><b>Control Total:</b> Apertura y cierre de años lectivos y periodos (trimestres/quimestres) con un solo clic.</li>
                <li><b>Seguridad de Datos:</b> El bloqueo de periodos cerrados impide modificaciones accidentales o no autorizadas de calificaciones históricas.</li>
            </ul>

            <h3>Matriculación y Cursos</h3>
            <ul>
                <li><b>Matrícula Simplificada:</b> Inscriba estudiantes en cursos y paralelos de forma rápida.</li>
                <li><b>Historial Académico:</b> Mantenga un registro detallado de todas las matrículas pasadas y presentes.</li>
            </ul>

            <h3>Calificaciones y Asistencia</h3>
            <ul>
                <li><b>Registro Ágil:</b> Los docentes pueden ingresar notas y asistencia desde cualquier dispositivo.</li>
                <li><b>Validaciones Automáticas:</b> El sistema alerta sobre notas fuera de rango y bloquea ingresos en fechas no permitidas.</li>
                <li><b>Reportes Instantáneos:</b> Generación automática de libretas de calificaciones y reportes de asistencia detallados (presentes, ausentes, atrasos).</li>
            </ul>
        </div>

        <!-- Module 2: Treasury -->
        <div class="module-block">
            <h2>2. Módulo de Tesorería</h2>
            <p>Optimice el flujo de caja y mantenga las cuentas claras con herramientas financieras integradas.</p>

            <h3>Gestión de Cobros</h3>
            <ul>
                <li><b>Cargos Automáticos:</b> Genere deudas mensuales (pensiones) a grupos de estudiantes masivamente.</li>
                <li><b>Estado de Cuenta:</b> Visualice rápidamente quién ha pagado y quién tiene saldos pendientes.</li>
            </ul>

            <h3>Facturación Electrónica e Impuestos</h3>
            <ul>
                <li><b>Cumplimiento SRI:</b> Emisión de facturas cumpliendo con la normativa ecuatoriana vigente.</li>
                <li><b>Descarga de Facturas:</b> Los padres de familia pueden descargar sus facturas en PDF directamente desde el portal.</li>
                <li><b>Múltiples Conceptos:</b> Gestión flexible de rubros (matrículas, pensiones, uniformes, etc.) con configuración de IVA personalizada.</li>
            </ul>
        </div>

        <!-- Module 3: Accounting -->
        <div class="module-block">
            <h2>3. Módulo Contable</h2>
            <p>Contabilidad robusta y automatizada, diseñada para cumplir con los estándares financieros y tributarios.</p>

            <h3>Plan de Cuentas y Asientos</h3>
            <ul>
                <li><b>Estructura Flexible:</b> Configure su plan de cuentas jerárquico según las necesidades de la institución.</li>
                <li><b>Automatización:</b> Los pagos y facturas generan asientos contables automáticamente, reduciendo errores manuales.</li>
            </ul>

            <h3>Reportes Financieros</h3>
            <ul>
                <li><b>Toma de Decisiones:</b> Genere Balances Generales y Estados de Resultados en tiempo real.</li>
                <li><b>Anexos Transaccionales (ATS):</b> Exporte la información necesaria para las declaraciones al SRI sin complicaciones.</li>
            </ul>
        </div>

        <!-- Module 4: Purchases -->
        <div class="module-block">
            <h2>4. Módulo de Compras</h2>
            <p>Control total sobre los egresos de la institución.</p>

            <h3>Proveedores y Gastos</h3>
            <ul>
                <li><b>Base de Datos de Proveedores:</b> Gestión centralizada de la información de sus proveedores.</li>
                <li><b>Registro de Facturas:</b> Ingrese facturas de compra y vincúlelas directamente a la contabilidad.</li>
            </ul>

            <h3>Retenciones</h3>
            <ul>
                <li><b>Emisión de Retenciones:</b> Genere comprobantes de retención automáticamente al registrar una compra, cumpliendo con la normativa fiscal.</li>
            </ul>
        </div>

        <!-- Module 5: Helpdesk & Communication -->
        <div class="module-block">
            <h2>5. Comunicación y Soporte</h2>
            <p>Mejore la interacción entre la institución, docentes y padres de familia.</p>

            <h3>Mesa de Ayuda (Helpdesk)</h3>
            <ul>
                <li><b>Gestión de Tickets:</b> Canales directos para reportar incidencias técnicas o administrativas.</li>
                <li><b>Seguimiento:</b> Monitoree el estado de sus solicitudes (Abierto, En Progreso, Resuelto) con notificaciones de cambio de estado.</li>
            </ul>

            <h3>Avisos y Cartelera</h3>
            <ul>
                <li><b>Comunicación Efectiva:</b> Publique anuncios importantes visibles para estudiantes, padres y docentes en su panel principal.</li>
            </ul>
        </div>

        <!-- Module 6: Security & Users -->
        <div class="module-block">
            <h2>6. Seguridad y Usuarios</h2>
            <p>Protección y control de acceso garantizado.</p>

            <ul>
                <li><b>Roles y Permisos:</b> Accesos diferenciados para Rectores, Administradores, Docentes, Estudiantes y Padres. Cada uno ve solo lo que necesita ver.</li>
                <li><b>Privacidad de Datos (ARCO):</b> Herramientas para gestionar los derechos de Acceso, Rectificación, Cancelación y Oposición de datos personales, cumpliendo con la ley de protección de datos.</li>
            </ul>
        </div>

        <div class="page-break"></div>

        <h1>Conclusión</h1>
        <p>ERP EDUCATIVA es más que un sistema; es un aliado estratégico para la excelencia educativa. Su arquitectura modular permite que la institución crezca y se adapte, asegurando siempre la integridad de la información y la eficiencia operativa.</p>
        <p>Para más información o soporte técnico, por favor utilice el módulo de Ayuda integrado en la plataforma.</p>

    </body>
    </html>
    """

    # Generate PDF
    result_file = open(output_filename, "wb")
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=result_file
    )
    result_file.close()

    if pisa_status.err:
        print(f"Error generating PDF: {pisa_status.err}")
    else:
        print(f"PDF generated successfully: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    generate_pdf()
