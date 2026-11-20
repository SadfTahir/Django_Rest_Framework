from django.urls import path

from .views import MakeViewSet, VehicleViewSet

list_actions = {'get': 'list', 'post': 'create'}
detail_actions = {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}

urlpatterns = [
    # v1 - Make
    path('v1/make/', MakeViewSet.as_view(list_actions), name='make-list'),
    path('v1/make/<int:pk>/', MakeViewSet.as_view(detail_actions), name='make-detail'),
    # v2 - Vehicle
    path('v2/vehicle/', VehicleViewSet.as_view(list_actions), name='vehicle-list'),
    path('v2/vehicle/<int:pk>/', VehicleViewSet.as_view(detail_actions), name='vehicle-detail'),
]
