from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'goals', views.GoalViewSet, basename='goal')

urlpatterns = [
    path('', views.home_view, name='home'),
    path('history/', views.history_view, name='history'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-code/<int:user_id>/', views.verify_code, name='verify_code'),
    path('change-password/', views.change_password, name='change_password'),

    path('add-account/', views.add_account, name='add_account'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('add-budget/', views.add_budget, name='add_budget'),
    path('add-goal/', views.add_goal, name='add_goal'),
    path('budgets/', views.budget_list, name='budget_list'),
    path('goals-history/', views.goals_history, name='goals_history'),
    path('contribute-goal/', views.contribute_to_goal, name='contribute_to_goal'),

    path('admin-panel/', views.admin_dashboard, name='admin_panel'),
    path('admin-panel/manage/<str:model_name>/', views.admin_manage_model, name='admin_manage'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]