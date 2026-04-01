import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from learning.models import LMSCourse, Module, Lesson
from users.models import Institution, User

def run():
    institution = Institution.objects.first()
    if not institution:
        print("No institution found.")
        return
        
    admin_user = User.objects.filter(role='ADMIN').first()
    
    # Create Course
    course, created = LMSCourse.objects.get_or_create(
        title="Revoluciona tu Productividad con IA: Herramientas Prácticas para Profesionales",
        institution=institution,
        defaults={
            'subtitle': 'Aplica la Inteligencia Artificial hoy mismo en Educación, Administración y Finanzas sin saber programar.',
            'description': 'Aprende a dominar la Inteligencia Artificial Generativa y transforma tu manera de trabajar. Este curso práctico te enseñará a crear prompts efectivos y automatizar tareas complejas.',
            'instructor': admin_user,
            'is_public': True,
            'price': 0.00
        }
    )
    
    if not created:
        print("Course already exists. Proceeding to update/clear modules.")
        course.modules.all().delete()
    
    # Module 1
    m1 = Module.objects.create(
        course=course,
        title="El Despertar (Derribando Mitos y Preparando el Terreno)",
        description="Eliminar el miedo a la tecnología y generar entusiasmo. Que entiendan que la IA no es una amenaza, sino el mejor asistente del mundo.",
        order=1
    )
    Lesson.objects.create(module=m1, title="La Promesa del Curso", content="Bienvenida directa. Mostrar un Antes y Después visual de cómo trabaja un profesional con y sin IA.\n\nEl Gancho: Al final de este curso, tendrás un asistente digital trabajando para ti gratis, 24/7.", order=1, duration_minutes=3)
    Lesson.objects.create(module=m1, title="¿Qué es realmente la IA Generativa?", content="Explicación con analogías simples de cómo funciona la Inteligencia Artificial sin usar terminología técnica o de algoritmos.", order=2, duration_minutes=5)
    Lesson.objects.create(module=m1, title="Conociendo a tu Nuevo Equipo", content="Tour rápido por las tres grandes herramientas gratuitas: ChatGPT, Claude y Google Gemini y sus casos de uso preferidos.", order=3, duration_minutes=6)

    # Module 2
    m2 = Module.objects.create(
        course=course,
        title="El Arte de Hablarle a la Máquina (Prompt Engineering)",
        description="Enseñar la habilidad más importante de la década: saber pedir las cosas.",
        order=2
    )
    Lesson.objects.create(module=m2, title="¿Por qué la IA me da malas respuestas?", content="El concepto de Basura entra, basura sale (Garbage in, garbage out).", order=1, duration_minutes=4)
    Lesson.objects.create(module=m2, title="La Fórmula Mágica 'C.R.E.A.'", content="Enseñar la estructura infalible para crear instrucciones profesionales:\n\n- Contexto (Quién eres y cuál es el escenario).\n- Rol (Actúa como un experto en...).\n- Especificidad (Tono, formato, longitud).\n- Acción (Lo que quieres que haga exactamente).", order=2, duration_minutes=8)
    Lesson.objects.create(module=m2, title="Demostración en Vivo: De un mal prompt a uno excelente", content="Demostración práctica de cómo cambia el resultado al aplicar la fórmula C.R.E.A.", order=3, duration_minutes=7)

    # Module 3
    m3 = Module.objects.create(
        course=course,
        title="Impacto Inmediato (Casos de Uso Reales)",
        description="Aquí es donde ocurre la magia. Ejemplos de aplicación inmediata en diferentes profesiones.",
        order=3
    )
    Lesson.objects.create(module=m3, title="IA para Educadores", content="Cómo crear una rúbrica de evaluación detallada, generación de ideas para clases y adaptación de textos complejos.", order=1, duration_minutes=10)
    Lesson.objects.create(module=m3, title="IA para Administradores y Directivos", content="Cómo redactar correos difíciles y resumir actas de reuniones largas en viñetas ejecutivas.", order=2, duration_minutes=10)
    Lesson.objects.create(module=m3, title="IA para Contadores y Financieros", content="Cómo explicar conceptos financieros complejos y extraer datos clave de contratos kilométricos. Importancia de la privacidad de los datos sensibles.", order=3, duration_minutes=10)

    # Module 4
    m4 = Module.objects.create(
        course=course,
        title="Los Límites y El Siguiente Nivel (El Gancho Final)",
        description="Dejarlos con la boca abierta y con la necesidad absoluta de tomar el Nivel 2.",
        order=4
    )
    Lesson.objects.create(module=m4, title="Lo que la IA NO puede hacer (y sus riesgos)", content="Privacidad de datos y la regla de oro: no subir datos confidenciales a IAs públicas. El problema de las alucinaciones.", order=1, duration_minutes=5)
    Lesson.objects.create(module=m4, title="Un Vistazo al Futuro (El Gran Enganche)", content="Automatizaciones en segundo plano. ¿Qué pasaría si tuvieras tu propio Agente de IA entrenado exclusivamente con los manuales de tu institución?\n\nPreparación para el Curso Nivel 2: Automatización y Creación de Agentes de IA.", order=2, duration_minutes=5)

    print(f"Course '{course.title}' created successfully with 4 modules and 11 lessons!")

if __name__ == '__main__':
    run()
