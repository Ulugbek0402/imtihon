from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('history/', views.history_view, name='history'),
    path('budgets/', views.budget_list, name='budget_list'),
    path('goals-history/', views.goals_history, name='goals_history'),

    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('contribute-goal/', views.contribute_to_goal, name='contribute_to_goal'),
    path('add-account/', views.add_account, name='add_account'),
    path('add-budget/', views.add_budget, name='add_budget'),
    path('add-goal/', views.add_goal, name='add_goal'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-code/<int:user_id>/', views.verify_code, name='verify_code'),

    path('admin-panel/', views.admin_dashboard, name='admin_panel'),
    path('admin-manage/<str:model_name>/', views.admin_manage_model, name='admin_manage_model'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    path('api/accounts/', views.AccountViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_accounts'),
    path('api/transactions/', views.TransactionViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_transactions'),
    path('api/goals/', views.GoalViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_goals'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]