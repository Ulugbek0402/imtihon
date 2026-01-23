from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('history/', views.TransactionHistoryView.as_view(), name='history'),
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('goals-history/', views.GoalsHistoryView.as_view(), name='goals_history'),

    path('add-transaction/', views.AddTransactionView.as_view(), name='add_transaction'),
    path('contribute-goal/', views.ContributeToGoalView.as_view(), name='contribute_to_goal'),
    path('add-account/', views.AddAccountView.as_view(), name='add_account'),
    path('add-budget/', views.AddBudgetView.as_view(), name='add_budget'),
    path('add-goal/', views.AddGoalView.as_view(), name='add_goal'),

    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-code/<int:user_id>/', views.VerifyCodeView.as_view(), name='verify_code'),

    path('admin-panel/', views.AdminDashboardView.as_view(), name='admin_panel'),
    path('delete-user/<int:user_id>/', views.DeleteUserView.as_view(), name='delete_user'),

    path('api/accounts/', views.AccountAPIView.as_view(), name='api_accounts'),
    path('api/transactions/', views.TransactionAPIView.as_view(), name='api_transactions'),
    path('api/goals/', views.GoalAPIView.as_view(), name='api_goals'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]