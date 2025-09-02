from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import (
    ExecutionRateListView, ExecutionRateCreateView, ExecutionRateUpdateView,
    ExecutionRateDetailView, ExecutionRateDeleteView
)

app_name = 'projects'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Project views
    path('projects/', views.project_list, name='project_list'),
    path('projects/add/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/export/', views.export_projects, name='export_projects'),
    path('projects/import/', views.import_projects, name='project_import'),
    
    # Execution Rate URLs
    path('execution-rates/', ExecutionRateListView.as_view(), name='execution_rate_list'),
    path('execution-rates/export/', views.export_execution_rates, name='execution_rate_export'),
    path('execution-rates/add/', ExecutionRateCreateView.as_view(), name='execution_rate_create'),
    path('execution-rates/<int:pk>/', ExecutionRateDetailView.as_view(), name='execution_rate_detail'),
    path('execution-rates/<int:pk>/edit/', ExecutionRateUpdateView.as_view(), name='execution_rate_edit'),
    path('execution-rates/<int:pk>/delete/', ExecutionRateDeleteView.as_view(), name='execution_rate_delete'),
]
