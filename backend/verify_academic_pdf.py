import os
import django
import sys

# Setup Django Environment
sys.path.append(r'c:\Users\Soporte\Documents\PROYECTOS NETFORCE\ERP EDUCATIVA\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academic.models import Enrollment
from django.test import RequestFactory
from academic.views import EnrollmentViewSet

def verify_report_card():
    print("--- Verifying Report Card PDF ---")
    
    # Get an enrollment
    enrollment = Enrollment.objects.first()
    if not enrollment:
        print("!!! No enrollment found. Create one first.")
        return

    print(f"Generating report for: {enrollment.student.get_full_name()} in {enrollment.course.name}")
    
    # Mock Request
    factory = RequestFactory()
    request = factory.get('/')
    request.user = enrollment.student # Simulate user
    
    # Instantiate ViewSet
    view = EnrollmentViewSet()
    view.request = request
    view.action_map = {'get': 'download_report_card'}
    
    # Call method directly
    try:
        # We need to set kwargs for get_object
        view.kwargs = {'pk': enrollment.id}
        
        response = view.download_report_card(request, pk=enrollment.id)
        
        if response.status_code == 200:
            content = response.content
            if content.startswith(b'%PDF'):
                print("   [SUCCESS] PDF generated successfully.")
                with open('test_report_card.pdf', 'wb') as f:
                    f.write(content)
                print("   Saved to test_report_card.pdf")
            else:
                print("   [FAILURE] Response is not a PDF.")
                print(content[:100])
        else:
             print(f"   [FAILURE] Status Code: {response.status_code}")
             print(response.content)
             
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"!!! Error: {e}")

if __name__ == "__main__":
    verify_report_card()
