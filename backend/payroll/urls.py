from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet, ContractViewSet, WorkShiftViewSet, 
    AttendanceViewSet, PayrollPeriodViewSet, DepartmentViewSet, PositionViewSet,
    PayrollRollViewSet
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'shifts', WorkShiftViewSet)
router.register(r'attendances', AttendanceViewSet)
router.register(r'periods', PayrollPeriodViewSet)
router.register(r'rolls', PayrollRollViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'positions', PositionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
