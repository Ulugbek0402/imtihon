from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'goals', views.GoalViewSet, basename='goal')

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/', include(router.urls)),
]