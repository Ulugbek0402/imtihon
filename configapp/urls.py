from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('history/', views.TransactionHistoryView.as_view(), name='history'),
    path('add-transaction/', views.AddTransactionView.as_view(), name='add_transaction'),

    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('admin-panel/', views.AdminDashboardView.as_view(), name='admin_panel'),
    path('admin-manage/<str:model_name>/', views.AdminManageModelView.as_view(), name='admin_manage_model'),

    path('api/accounts/', views.AccountViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_accounts'),
    path('api/transactions/', views.TransactionViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='api_transactions'),
    path('api/goals/', views.GoalViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_goals'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]