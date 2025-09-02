from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Project

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    list_display = ('code', 'program', 'location', 'district', 'start_year', 'estimated_cost')
    list_filter = ('start_year', 'district', 'property_status')
    search_fields = ('code', 'program', 'location', 'district', 'planning_code')
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('code', 'program', 'projects', 'location', 'district', 'planning_code')
        }),
        ('تفاصيل المشروع', {
            'fields': ('components', 'target_group', 'property_status', 'property_drawing', 'area', 'property_prep_cost')
        }),
        ('الدراسات والإنجازات', {
            'fields': ('studies', 'achievements', 'estimated_cost', 'start_year', 'estimated_duration')
        }),
        ('المعلومات المالية', {
            'fields': ('implementation_years', 'budget_years')
        }),
        ('المؤشرات', {
            'fields': ('indicator_1', 'indicator_2', 'indicator_3')
        }),
        ('الشركاء والتمويل', {
            'fields': ('potential_partners', 'funding_sources')
        }),
    )
