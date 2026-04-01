import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from learning.models import LMSCourse, Lesson

def run():
    try:
        course = LMSCourse.objects.get(title="Revoluciona tu Productividad con IA: Herramientas Prácticas para Profesionales")
        lesson = Lesson.objects.get(module__course=course, title="La Promesa del Curso")
        
        content = """# La Promesa del Curso

**Bienvenido a la revolución de la Productividad con IA.**

¿Sientes que a tu día le faltan horas? Entre planificar clases, redactar correos complejos, cuadrar números o estructurar informes, el trabajo operativo nos consume. **Pero esto está a punto de cambiar.**

### Una Nueva Era: La IA Generativa
Durante décadas, la Inteligencia Artificial parecía ciencia ficción, algo exclusivo para ingenieros en laboratorios. Sin embargo, hemos llegado a un punto de inflexión histórico. La IA ha evolucionado enormemente.

En su etapa actual, ya no hablamos de máquinas calculadoras. Hablamos de **IA Generativa**. Una tecnología capaz de:
*   **Entender** el contexto.
*   **Razonar** ante diferentes situaciones.
*   **Redactar y Crear** documentos por ti.
*   **Resumir** información extensa en segundos.

Hoy, la IA tiene la capacidad de ser **el asistente más brillante, rápido y eficiente** que jamás hayas tenido.

### Nuestra Promesa en Eduka360
El objetivo central de este curso es enseñarte a sacarle el máximo provecho a esta revolución tecnológica. 

**No te vamos a enseñar a programar**. Te vamos a enseñar a usar herramientas prácticas de IA aplicadas directamente a tu profesión. Aprenderás:
1.  Qué es exactamente esta tecnología y cómo funciona de forma intuitiva.
2.  Cómo darle instrucciones precisas y conseguir resultados espectaculares.
3.  Cómo delegarle tareas repetitivas *hoy mismo* para ahorrarte horas de trabajo cada semana.

> 💡 **Recuerda:** La IA no te va a reemplazar, pero un profesional que sabe usar la IA, sí lo hará.

### Tu Primer Paso
Este curso introductorio es tu puerta de entrada. Es un primer escalón fundamental para dominar herramientas que transformarán tu carrera, preparándote para la automatización y creación avanzada de agentes que veremos en niveles posteriores.

Así que, cierra el resto de tus pestañas, prepara tu café y acompáñanos a la siguiente lección. **¡Vamos a conocer a tu nuevo equipo de trabajo digital!**
"""
        
        lesson.content = content
        lesson.save()
        print("Lesson 1 updated successfully with professional markdown content!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run()
