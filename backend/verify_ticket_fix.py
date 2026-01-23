import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from helpdesk.models import Ticket, TicketComment, TicketAttachment, ServiceCatalog
from users.models import User, Institution
from helpdesk.serializers import TicketSerializer

def verify_fix():
    print("Verifying ticket fixes...")
    
    # 1. Setup Data
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found, cannot test.")
        return
        
    institution = Institution.objects.first()
    if not institution:
        # Create a dummy institution if needed, but likely exists
        institution = Institution.objects.create(name="Test Inst", ruc="1234567890001")
        
    category, _ = ServiceCatalog.objects.get_or_create(
        institution=institution,
        name="Test Category",
        defaults={'description': 'For testing'}
    )
    
    # 2. Test Ticket Creation
    ticket = Ticket.objects.create(
        institution=institution,
        requester=user,
        category=category,
        title="Test Ticket",
        description="Testing fixes",
        status='OPEN'
    )
    print(f"Created ticket #{ticket.id} with status {ticket.status}")
    
    # 3. Test Status Update via Serializer (mimicking API)
    # The fix was in the serializer not being read-only for status
    data = {'status': 'IN_PROGRESS'}
    serializer = TicketSerializer(instance=ticket, data=data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        ticket.refresh_from_db()
        if ticket.status == 'IN_PROGRESS':
            print("SUCCESS: Status updated to IN_PROGRESS via serializer.")
        else:
            print(f"FAILURE: Status is {ticket.status}, expected IN_PROGRESS.")
    else:
        print(f"FAILURE: Serializer validation failed: {serializer.errors}")

    # 4. Test Comment Addition (Backend Model/View logic check)
    # We added the frontend service method, but let's verify the backend accepts creating comments 
    # directly via model/serializer as the view would.
    # The view 'TicketCommentViewSet' allows create.
    
    comment_content = "This is a test comment."
    comment = TicketComment.objects.create(
        ticket=ticket,
        author=user,
        content=comment_content
    )
    if comment.id:
        print(f"SUCCESS: Comment created with id {comment.id}")
    else:
        print("FAILURE: Could not create comment")

    # 5. Test Attachment
    # Mock a file
    file_content = b"test content"
    test_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")
    
    attachment = TicketAttachment.objects.create(
        ticket=ticket,
        uploaded_by=user,
        file=test_file
    )
    if attachment.id:
        print(f"SUCCESS: Attachment created with id {attachment.id}")
    else:
        print("FAILURE: Could not create attachment")

if __name__ == '__main__':
    try:
        verify_fix()
    except Exception as e:
        print(f"An error occurred: {e}")
