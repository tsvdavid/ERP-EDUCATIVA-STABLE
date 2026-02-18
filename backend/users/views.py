from rest_framework import viewsets, permissions
from .models import Institution, User
from .serializers import InstitutionSerializer, UserSerializer, UserCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import CanManageInstitution, IsAdminUser, IsRectorUser

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['institution'] = user.institution.id if user.institution else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInstitution]

    def get_queryset(self):
        # Single Tenant: Return all (usually just one)
        return Institution.objects.all()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        from .permissions import CanManageUser
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanManageUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        try:
            queryset = User.objects.all().select_related('institution').prefetch_related('children')
            role = self.request.query_params.get('role', None)
            if role:
                queryset = queryset.filter(role=role)
                # Restriction for Teachers viewing Students
                if role == 'STUDENT' and self.request.user.role == 'TEACHER':
                    # Filter students enrolled in courses where the teacher teaches a subject
                    # Path: User -> enrollments -> course -> subjects -> teacher
                    queryset = queryset.filter(enrollments__course__subjects__teacher=self.request.user).distinct()
            
            # Header Filter
            header_inst_id = self.request.headers.get('X-Institution-ID')
            
            # Security Check: If user is not Admin, they can ONLY access their own institution
            user = self.request.user
            if not user.is_superuser and user.role != 'ADMIN':
                 if user.institution:
                     # Force filter to user's institution
                     queryset = queryset.filter(institution=user.institution)
                     if header_inst_id and str(header_inst_id) != str(user.institution.id):
                         return queryset.none()
                 else:
                     # Non-admin users without institution should see NOTHING
                     return queryset.none()
            elif header_inst_id and str(header_inst_id).isdigit():
                queryset = queryset.filter(institution_id=int(header_inst_id))

            return queryset
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
