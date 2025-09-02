from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.db.models import Q, Sum, F, Case, When, Value, IntegerField, CharField
from django.db.models.functions import Concat, Coalesce
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, requires_csrf_token
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.db import transaction
import json
import pandas as pd
import tablib
from tablib import Dataset
from django.conf import settings
import os
from .models import Project, ExecutionRate
from .forms import ProjectForm, ProjectImportForm, ExecutionRateForm
from .resources import ProjectResource
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

# Home View
def home(request):
    context = {
        'title': _('نظام إدارة المشاريع'),
    }
    return render(request, 'projects/home.html', context)

# Custom 404 Error Handler
def custom_404(request, exception):
    return render(request, '404.html', status=404)

# Custom 500 Error Handler
@requires_csrf_token
def server_error(request, template_name='500.html'):
    return HttpResponseServerError(render(request, '500.html'))

# Project List View
def project_detail(request, pk):
    """Display a single project's details."""
    project = get_object_or_404(Project, pk=pk)
    context = {
        'title': _('تفاصيل المشروع') + f' - {project.code}',
        'project': project,
    }
    return render(request, 'projects/project_detail.html', context)

def project_list(request):
    # Prevent browser from caching this page
    if hasattr(request, 'session'):
        request.session['django_timezone'] = timezone.get_current_timezone_name()
    
    # Force a fresh database query
    from django.db import connection
    connection.close()
    
    query = request.GET.get('q', '')
    year = request.GET.get('year', '')
    
    # Use select_related or prefetch_related if there are related fields
    projects = Project.objects.all().order_by('-id')
    
    # Generate years from 2022 to 2028 for the year filter dropdown
    years = list(range(2022, 2029))  # 2028 is included
    years = [str(year) for year in years]
    
    if query:
        projects = projects.filter(
            Q(code__icontains=query) |
            Q(program__icontains=query) |
            Q(location__icontains=query) |
            Q(district__icontains=query)
        )
    
    if year:
        projects = projects.filter(start_year=year)
    
    # Add debug information
    debug_info = {
        'project_count': projects.count(),
        'query': query,
        'year': year,
        'timestamp': timezone.now().isoformat(),
    }
    print(f"Debug - Project List: {debug_info}")
    
    context = {
        'title': _('قائمة المشاريع'),
        'projects': projects,
        'search_query': query,
        'years': years,
        'selected_year': year,
        'cache_buster': int(timezone.now().timestamp()),  # Add timestamp to prevent caching
        'debug_info': debug_info,  # For debugging
    }
    
    response = render(request, 'projects/project_list.html', context)
    # Add headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'  # HTTP 1.1
    response['Pragma'] = 'no-cache'  # HTTP 1.0
    response['Expires'] = '0'  # Proxies
    response['X-Content-Type-Options'] = 'nosniff'  # Prevent MIME-type sniffing
    return response

# Project Create View
@require_http_methods(["GET", "POST"])
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.save()
            messages.success(request, _('تمت إضافة المشروع بنجاح'))
            return redirect('projects:project_list')
    else:
        form = ProjectForm()
    
    context = {
        'title': _('إضافة مشروع جديد'),
        'form': form,
    }
    return render(request, 'projects/project_form.html', context)

# Project Edit View
@require_http_methods(["GET", "POST"])
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        print("Form data received:", request.POST)  # Log form data
        form = ProjectForm(request.POST, instance=project)
        
        if not form.is_valid():
            # Log all form errors in detail
            print("Form validation failed. Errors:")
            for field, errors in form.errors.items():
                field_label = form.fields[field].label if field in form.fields else field
                print(f"- {field_label}: {', '.join(errors)}")
                
            # Log cleaned data that did pass validation
            try:
                print("Cleaned data:", form.cleaned_data)
            except Exception as e:
                print("Could not get cleaned_data:", str(e))
                
            messages.error(request, _('حدث خطأ في التحقق من صحة البيانات. يرجى تصحيح الأخطاء أدناه.'))
        else:
            try:
                # Save the form data
                project = form.save(commit=False)
                project.save()
                
                # Force an immediate database update
                from django.db import connection
                connection.close()
                
                messages.success(request, _('تم تحديث المشروع بنجاح'))
                print(f"Project {project.id} saved successfully")
                
                # Use HttpResponseRedirect to force a fresh GET request
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(reverse('projects:project_list'))
                
            except Exception as e:
                error_msg = f'حدث خطأ أثناء حفظ التغييرات: {str(e)}'
                messages.error(request, error_msg)
                print(f"Error saving project: {str(e)}")
                if hasattr(e, '__traceback__'):
                    import traceback
                    traceback.print_exc()
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'title': _('تعديل المشروع'),
        'form': form,
        'project': project,
        'cache_buster': int(timezone.now().timestamp()),
    }
    return render(request, 'projects/project_form.html', context)

# Project Delete View
@require_http_methods(["POST"])
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()
    messages.success(request, _('تم حذف المشروع بنجاح'))
    return redirect('projects:project_list')

# Execution Rate Views
class ExecutionRateListView(ListView):
    model = ExecutionRate
    template_name = 'projects/execution_rate_list.html'
    context_object_name = 'execution_rates'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('project')
        
        # Get filter parameters
        code = self.request.GET.get('code')
        project_name = self.request.GET.get('project')
        
        # Apply filters
        if code:
            queryset = queryset.filter(project__code__icontains=code)
        if project_name:
            queryset = queryset.filter(Q(project__program__icontains=project_name) | 
                                     Q(project__projects__icontains=project_name))
            
        # Order by most recent first
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('معدلات التنفيذ')
        context['code_filter'] = self.request.GET.get('code', '')
        context['project_filter'] = self.request.GET.get('project', '')
        return context


def export_execution_rates(request):
    """Export execution rates to Excel with Arabic headers"""
    from django.http import HttpResponse
    import xlwt
    from django.utils import timezone
    from django.utils.encoding import smart_str
    from django.db.models import Q
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="execution_rates_%s.xls"' % timezone.now().strftime('%Y-%m-%d')
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('معدلات التنفيذ')
    
    # Set RTL direction
    ws.set_right_to_left()
    
    # Set font for Arabic text
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    # Define columns
    columns = [
        ('الرمز', 20),
        ('المشروع', 40),
        ('المبلغ المبرمج', 20),
        ('مساهمة الشركاء', 20),
        ('التكاليف الفعلية', 20),
        ('التكاليف التقديرية', 20),
        ('نسبة الإنجاز المالي', 20),
        ('تاريخ الإضافة', 20),
    ]
    
    # Write headers
    for col_num, (header, width) in enumerate(columns):
        ws.col(col_num).width = 256 * width  # Set column width
        ws.write(0, col_num, header, font_style)
    
    # Get filtered data
    execution_rates = ExecutionRate.objects.select_related('project').order_by('-created_at')
    
    # Apply filters if any
    code = request.GET.get('code')
    project_name = request.GET.get('project')
    
    if code:
        execution_rates = execution_rates.filter(project__code__icontains=code)
    if project_name:
        execution_rates = execution_rates.filter(
            Q(project__program__icontains=project_name) | 
            Q(project__projects__icontains=project_name)
        )
    
    # Write data rows
    for row_num, rate in enumerate(execution_rates, 1):
        ws.write(row_num, 0, smart_str(rate.project.code if rate.project else ''))
        ws.write(row_num, 1, smart_str(rate.project.program if rate.project else ''))
        ws.write(row_num, 2, str(rate.programmed_amount) if rate.programmed_amount else '')
        ws.write(row_num, 3, str(rate.partner_contribution) if rate.partner_contribution else '')
        ws.write(row_num, 4, str(rate.actual_costs) if rate.actual_costs else '')
        ws.write(row_num, 5, str(rate.estimated_costs) if rate.estimated_costs else '')
        ws.write(row_num, 6, f"{rate.financial_achievement_percentage}%" if rate.financial_achievement_percentage else '')
        
        # Handle date field - convert to string to avoid timezone issues
        if rate.created_at:
            if timezone.is_aware(rate.created_at):
                # Convert to local timezone and format as string
                local_dt = timezone.localtime(rate.created_at)
                ws.write(row_num, 7, local_dt.strftime('%Y-%m-%d'))
            else:
                ws.write(row_num, 7, rate.created_at.strftime('%Y-%m-%d'))
        else:
            ws.write(row_num, 7, '')
    
    wb.save(response)
    return response


class ExecutionRateCreateView(CreateView):
    model = ExecutionRate
    form_class = ExecutionRateForm
    template_name = 'projects/execution_rate_form.html'
    
    def form_valid(self, form):
        try:
            # Save the form and the object
            self.object = form.save(commit=True)
            messages.success(self.request, _('تم إضافة معدل التنفيذ بنجاح'))
            # Redirect to the list view immediately after saving
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, _(f'حدث خطأ أثناء الحفظ: {str(e)}'))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log form errors for debugging
        print("Form errors:", form.errors)
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('projects:execution_rate_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة معدل تنفيذ جديد')
        return context


class ExecutionRateUpdateView(UpdateView):
    model = ExecutionRate
    form_class = ExecutionRateForm
    template_name = 'projects/execution_rate_form.html'
    
    def get_success_url(self):
        messages.success(self.request, _('تم تحديث معدل التنفيذ بنجاح'))
        return reverse('execution_rate_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل معدل التنفيذ')
        return context


class ExecutionRateDetailView(DetailView):
    model = ExecutionRate
    template_name = 'projects/execution_rate_detail.html'
    context_object_name = 'execution_rate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تفاصيل معدل التنفيذ')
        return context


class ExecutionRateDeleteView(DeleteView):
    model = ExecutionRate
    template_name = 'projects/execution_rate_confirm_delete.html'
    success_url = reverse_lazy('execution_rate_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف معدل التنفيذ بنجاح'))
        return super().delete(request, *args, **kwargs)


# Export Views
from django.http import HttpResponse, HttpResponseBadRequest
import xlwt
from xlwt import XFStyle, easyxf
from datetime import datetime
import io

def export_execution_rates(request):
    """
    Export execution rates data to Excel file
    """
    # Get filter parameters
    search_query = request.GET.get('q', '')
    
    # Filter execution rates based on search query
    execution_rates = ExecutionRate.objects.select_related('project').all()
    
    if search_query:
        execution_rates = execution_rates.filter(
            Q(project__code__icontains=search_query) |
            Q(project__program__icontains=search_query) |
            Q(project__projects__icontains=search_query)
        )
    
    # Create the workbook and add a worksheet
    output = io.BytesIO()
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('معدلات التنفيذ')
    
    # Create a font that supports Arabic
    font = xlwt.Font()
    font.name = 'Arial'
    font.height = 220  # 11pt
    
    # Set RTL alignment for all cells
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_RIGHT
    alignment.vert = xlwt.Alignment.VERT_CENTER
    
    # Create styles for header cells
    header_style = xlwt.XFStyle()
    header_font = xlwt.Font()
    header_font.bold = True
    header_font.height = 220  # 11pt
    header_font.colour_index = xlwt.Style.colour_map['white']  # White text
    header_style.font = header_font
    header_style.alignment.horz = xlwt.Alignment.HORZ_CENTER
    header_style.alignment.vert = xlwt.Alignment.VERT_CENTER
    header_style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    header_style.pattern.pattern_fore_colour = xlwt.Style.colour_map['dark_blue']  # Dark blue background
    
    # Define number format
    number_style = xlwt.XFStyle()
    number_style.num_format_str = '#,##0.00'
    
    # Define percent format
    percent_style = xlwt.XFStyle()
    percent_style.num_format_str = '0.00%'
    
    # Define date format
    date_style = xlwt.XFStyle()
    date_style.num_format_str = 'yyyy-mm-dd'
    
    # Write headers
    headers = [
        'رمز المشروع',
        'البرنامج',
        'المشاريع',
        'المبلغ المبرمج',
        'تعبئة الشركاء',
        'تاريخ البرمجة',
        'تاريخ إطلاق الصفقات',
        'التكاليف الفعلية (أ)',
        'التكاليف التقديرية (ب)',
        'فرق التكلفة (%)',
        'تاريخ الانتهاء المتوقع',
        'تاريخ البداية الفعلية',
        'تاريخ الانتهاء الفعلي',
        'فرق المدة (بالأيام)',
        'معدل التأخير (%)',
        'معدل التقدم (%) للأشغال',
        'معدل الإنجاز (%) (مالي)',
        'تاريخ الإنشاء',
        'آخر تحديث'
    ]
    
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, header_style)
    
    # Write data rows
    for row_num, rate in enumerate(execution_rates, 1):
        ws.write(row_num, 0, rate.project.code)
        ws.write(row_num, 1, rate.project.program)
        ws.write(row_num, 2, rate.project.projects)
        # Helper function to format date safely
        def format_date(dt):
            if dt is None:
                return ''
            if hasattr(dt, 'utcoffset'):  # Check if it's a datetime object
                if timezone.is_aware(dt):
                    dt = timezone.localtime(dt)
                return dt.strftime('%Y-%m-%d')
            # It's a date object
            return dt.strftime('%Y-%m-%d')
            
        ws.write(row_num, 3, float(rate.programmed_amount or 0), number_style)
        ws.write(row_num, 4, float(rate.partner_contribution or 0), number_style)
        ws.write(row_num, 5, format_date(rate.programming_date))
        ws.write(row_num, 6, format_date(rate.market_launch_date))
        ws.write(row_num, 7, float(rate.actual_costs or 0), number_style)
        ws.write(row_num, 8, float(rate.estimated_costs or 0), number_style)
        ws.write(row_num, 9, float(rate.cost_difference_percentage or 0) / 100, percent_style)
        ws.write(row_num, 10, format_date(rate.expected_end_date))
        ws.write(row_num, 11, format_date(rate.actual_start_date))
        ws.write(row_num, 12, format_date(rate.actual_end_date))
        ws.write(row_num, 13, rate.duration_difference_days or 0, number_style)
        ws.write(row_num, 14, float(rate.delay_percentage or 0) / 100, percent_style)
        ws.write(row_num, 15, float(rate.work_progress_percentage or 0) / 100, percent_style)
        ws.write(row_num, 16, float(rate.financial_achievement_percentage or 0) / 100, percent_style)
        ws.write(row_num, 17, format_date(rate.created_at))
        ws.write(row_num, 18, format_date(rate.updated_at))
    
    # Set column widths
    for i in range(len(headers)):
        ws.col(i).width = 4000  # 4000 = 40 * 256 (units of 1/256 of a character width)
    
    # Save the workbook to the output buffer
    wb.save(output)
    output.seek(0)
    
    # Prepare the response
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'execution_rates_export_{timestamp}.xls'
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.ms-excel'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
from datetime import datetime

def project_import_preview(request):
    if request.method == 'POST':
        form = ProjectImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Process the file
            file = request.FILES['file']
            
            # Check file extension
            if not file.name.lower().endswith(('.xls', '.xlsx')):
                messages.error(request, _('الرجاء تحميل ملف Excel صالح (ملفات xls أو xlsx فقط)'))
                return redirect('projects:project_import')
            
            # Read the Excel file with appropriate format
            file_format = 'xlsx' if file.name.lower().endswith('.xlsx') else 'xls'
            
            try:
                dataset = tablib.Dataset()
                dataset.load(file.read(), format=file_format)
            except Exception as e:
                messages.error(request, _('خطأ في قراءة الملف. يرجى التأكد من صحة تنسيق الملف.'))
                return redirect('projects:project_import')
            
            if not dataset:
                messages.error(request, _('الملف فارغ أو لا يحتوي على بيانات'))
                return redirect('projects:project_import')
            
            # Get headers and data
            headers = dataset.headers
            data = dataset.dict
            
            # Process data and create preview
            preview_data = []
            for row in data[:10]:  # Show first 10 rows for preview
                preview_data.append(dict(zip(headers, row)))
            
            # Store data in session for final import
            request.session['import_data'] = dataset.export('json')
            request.session['import_headers'] = headers
            
            return render(request, 'projects/import_preview.html', {
                'headers': headers,
                'preview_data': preview_data,
                'total_rows': len(data),
                'form': form
            })
            
    else:
        form = ProjectImportForm()
    
    return render(request, 'projects/import.html', {'form': form})

def import_projects(request):
    if request.method == 'POST':
        try:
            if 'file' not in request.FILES:
                messages.error(request, _('الرجاء تحديد ملف للتحميل'))
                return redirect('projects:project_import')
                
            # Get the uploaded file
            new_projects = request.FILES['file']
            
            # Check file extension
            if not new_projects.name.lower().endswith(('.xls', '.xlsx')):
                messages.error(request, _('الرجاء تحميل ملف Excel صالح (ملفات xls أو xlsx فقط)'))
                return redirect('projects:project_import')
            
            try:
                # First try with pandas for better error handling
                if new_projects.name.lower().endswith('.xlsx'):
                    df = pd.read_excel(new_projects, engine='openpyxl')
                else:
                    df = pd.read_excel(new_projects, engine='xlrd')
                
                # Replace NaN with None and convert to list of dictionaries
                records = df.replace({pd.NA: None}).to_dict('records')
                imported_data = tablib.Dataset()
                
                if len(records) > 0:
                    # Get headers from the first record
                    headers = list(records[0].keys())
                    imported_data.headers = headers
                    
                    # Process each row
                    for record in records:
                        row = []
                        for header in headers:
                            value = record.get(header)
                            # Handle JSON fields
                            if header in ['implementation_years', 'budget_years'] and value is not None:
                                if isinstance(value, str):
                                    try:
                                        value = json.loads(value)
                                    except (ValueError, TypeError):
                                        value = [str(value)] if value else []
                                elif not isinstance(value, (list, tuple)):
                                    value = [str(value)]
                            row.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
                        imported_data.append(row)
                
            except Exception as e:
                # If pandas fails, try with tablib directly
                try:
                    new_projects.seek(0)  # Reset file pointer
                    file_format = 'xlsx' if new_projects.name.lower().endswith('.xlsx') else 'xls'
                    dataset = tablib.Dataset()
                    imported_data = dataset.load(new_projects.read(), format=file_format)
                except Exception as e2:
                    error_msg = f'خطأ في قراءة الملف: {str(e2)}'
                    if 'Unsupported format' in str(e2) or 'not a zip file' in str(e2).lower():
                        error_msg = 'تنسيق الملف غير مدعوم. يرجى التأكد من أن الملف صحيح وغير تالف.'
                    messages.error(request, error_msg)
                    return redirect('projects:project_import')
            
            if not imported_data or len(imported_data) == 0:
                messages.error(request, _('الملف فارغ أو لا يحتوي على بيانات'))
                return redirect('projects:project_import')
            
            # Import the data using the resource with update strategy
            project_resource = ProjectResource()
            
            # First, get all existing project codes for duplicate checking
            existing_codes = set(Project.objects.values_list('code', flat=True))
            
            # Process each row individually to handle duplicates
            result = None
            for row in imported_data.dict:
                try:
                    # Skip if this is a duplicate code and we're not updating
                    if row.get('code') in existing_codes:
                        messages.warning(request, 
                            f'تم تخطي المشروع بالرمز {row.get("code")} لأنه موجود مسبقاً')
                        continue
                        
                    # Import the row
                    row_dataset = tablib.Dataset()
                    row_dataset.headers = imported_data.headers
                    row_dataset.append([row.get(h) for h in imported_data.headers])
                    
                    result = project_resource.import_data(
                        row_dataset, 
                        dry_run=False, 
                        raise_errors=True,
                        collect_failed_rows=True
                    )
                    
                    # Add the new code to our set to prevent duplicates in the same import
                    if row.get('code'):
                        existing_codes.add(row.get('code'))
                        
                except Exception as e:
                    messages.error(request, 
                        f'خطأ في استيراد السطر: {str(e)}')
            
            # Show success message if we processed any rows
            if result and (result.has_errors() or result.has_validation_errors()):
                error_messages = []
                for error in result.base_errors:
                    error_messages.append(f'خطأ: {error.error}')
                for row_num, errors in result.row_errors():
                    for error in errors:
                        error_messages.append(f'خطأ في السطر {row_num + 2}: {error.error}')
                
                for msg in error_messages[:5]:  # Show first 5 errors to avoid message flooding
                    messages.error(request, msg)
                if len(error_messages) > 5:
                    messages.warning(request, f'و {len(error_messages) - 5} أخطاء إضافية...')
                
                return redirect('projects:project_import')
            
            # If we get here, import was successful
            messages.success(request, _(f'تم استيراد {len(imported_data)} سجل بنجاح'))
            return redirect('projects:project_list')
            
        except Exception as e:
            import traceback
            error_message = f'حدث خطأ غير متوقع: {str(e)}\n{traceback.format_exc()}'
            messages.error(request, _('حدث خطأ أثناء معالجة الملف. يرجى التأكد من صحة البيانات والمحاولة مرة أخرى.'))
            return redirect('projects:project_import')
    
    return render(request, 'projects/import.html', {'title': _('استيراد مشاريع')})

def export_projects(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="projects_export_{datetime.now().strftime("%Y%m%d_%H%M")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('المشاريع')
    
    # Define styles
    # ==============
    # 1. Header Style
    header_style = xlwt.XFStyle()
    
    # Font
    font = xlwt.Font()
    font.bold = True
    font.colour_index = xlwt.Style.colour_map['white']
    font.height = 220  # Slightly larger font for headers
    header_style.font = font
    
    # Set RTL direction for the sheet
    ws.set_panes_frozen(True)
    ws.set_show_grid(False)
    ws.right_to_left = True  # Enable RTL for the entire sheet
    
    # Alignment
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_CENTER
    alignment.vert = xlwt.Alignment.VERT_CENTER
    alignment.wrap = 1  # Wrap text
    alignment.rtl = 1  # Right-to-left
    header_style.alignment = alignment
    
    # Border
    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN
    borders.left_colour = xlwt.Style.colour_map['white']
    borders.right_colour = xlwt.Style.colour_map['white']
    borders.top_colour = xlwt.Style.colour_map['white']
    borders.bottom_colour = xlwt.Style.colour_map['white']
    header_style.borders = borders
    
    # Background - Dark gray for professional look
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray50']  # Dark gray background
    header_style.pattern = pattern
    
    # Font - White and bold for better contrast
    font = xlwt.Font()
    font.bold = True
    font.colour_index = xlwt.Style.colour_map['white']
    font.height = 220  # Slightly larger font for headers
    header_style.font = font
    
    # ==============
    # 2. Data Row Style - White background for all data rows
    data_style = xlwt.XFStyle()
    
    # Font
    font = xlwt.Font()
    font.height = 200
    data_style.font = font
    
    # Alignment
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_RIGHT
    alignment.vert = xlwt.Alignment.VERT_CENTER
    alignment.wrap = 1  # Wrap text
    alignment.rtl = 1  # Right-to-left
    data_style.alignment = alignment
    
    # Border
    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN
    data_style.borders = borders
    
    # Set white background for all data rows
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['white']
    data_style.pattern = pattern
    
    # ==============
    # 3. Alternate Row Style (for better readability)
    alt_data_style = xlwt.XFStyle()
    
    # Font
    font = xlwt.Font()
    font.height = 200
    alt_data_style.font = font
    
    # Alignment
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_RIGHT
    alignment.vert = xlwt.Alignment.VERT_CENTER
    alignment.wrap = 1  # Wrap text
    alignment.rtl = 1  # Right-to-left
    alt_data_style.alignment = alignment
    
    # Border
    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN
    alt_data_style.borders = borders
    
    # Light gray background for alternate rows
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']  # Changed from 'light_gray' to 'gray25'
    alt_data_style.pattern = pattern
    
    # Set RTL direction for the sheet
    ws.set_panes_frozen(True)
    ws.set_show_grid(False)
    ws.right_to_left = 1  # This makes the sheet RTL
    
    # Create resource and get all data
    project_resource = ProjectResource()
    queryset = Project.objects.all().select_related()
    dataset = project_resource.export(queryset)
    
    # Custom Arabic headers in right-to-left order (rightmost column first)
    arabic_headers = [
        'مصادر التمويل المحتملة',
        'الشركاء المحتملين',
        'المؤشر 3',
        'المؤشر 2',
        'المؤشر 1',
        'سنوات الميزانية',
        'سنوات التنفيذ',
        'المدة التقديرية(أشهر)',
        'سنة الانطلاق',
        'التكلفة التقديرية',
        'الإنجازات',
        'الدراسات',
        'كلفة تعبئة العقار',
        'المساحة',
        'الرسم العقاري',
        'وضعية العقار',
        'الفئة المستهدفة',
        'مكونات المشروع',
        'الرمز في تصميم التهيئة',
        'المقاطعة/الجماعة',
        'المكان',
        'المشاريع',
        'البرنامج',
        'الرمز',
        'الاهداف التنموية'
    ]
    
    # Set column widths and write headers with right alignment
    column_widths = {
        'الرمز': 2000,
        'البرنامج': 4000,
        'المشاريع': 6000,
        'المكان': 4000,
        'المقاطعة/الجماعة': 4000,
        'الرمز في تصميم التهيئة': 4000,
        'مكونات المشروع': 6000,
        'الفئة المستهدفة': 4000,
        'وضعية العقار': 4000,
        'الرسم العقاري': 4000,
        'المساحة': 3000,
        'كلفة تعبئة العقار': 4000,
        'الدراسات': 5000,
        'الإنجازات': 6000,
        'التكلفة التقديرية': 4000,
        'سنة الانطلاق': 3000,
        'المدة التقديرية(أشهر)': 4000,
        'سنوات التنفيذ': 4000,
        'سنوات الميزانية': 4000,
        'المؤشر 1': 4000,
        'المؤشر 2': 4000,
        'المؤشر 3': 4000,
        'الشركاء المحتملين': 5000,
        'مصادر التمويل المحتملة': 5000,
        'الاهداف التنموية': 6000
    }
    
    # Write headers with styling
    for col_num, header in enumerate(arabic_headers):
        # Set column width
        ws.col(col_num).width = column_widths.get(header, 4000)  # Default width 4000
        
        # Write header with style
        ws.write(0, col_num, header, header_style)
        
        # Set row height for header
        ws.row(0).height_mismatch = True
        ws.row(0).height = 500  # Slightly taller row for headers
    
    # Map between Arabic headers and model field names (order matches the arabic_headers list)
    field_map = {
        'مصادر التمويل المحتملة': 'funding_sources',
        'الشركاء المحتملين': 'potential_partners',
        'المؤشر 3': 'indicator_3',
        'المؤشر 2': 'indicator_2',
        'المؤشر 1': 'indicator_1',
        'سنوات الميزانية': 'budget_years',
        'سنوات التنفيذ': 'implementation_years',
        'المدة التقديرية(أشهر)': 'estimated_duration',
        'سنة الانطلاق': 'start_year',
        'التكلفة التقديرية': 'estimated_cost',
        'الإنجازات': 'achievements',
        'الدراسات': 'studies',
        'كلفة تعبئة العقار': 'property_prep_cost',
        'المساحة': 'area',
        'الرسم العقاري': 'property_drawing',
        'وضعية العقار': 'property_status',
        'الفئة المستهدفة': 'target_group',
        'مكونات المشروع': 'components',
        'الرمز في تصميم التهيئة': 'planning_code',
        'المقاطعة/الجماعة': 'district',
        'المكان': 'location',
        'المشاريع': 'projects',
        'البرنامج': 'program',
        'الرمز': 'code',
        'الاهداف التنموية': 'development_goals',  # Add this field to your model if it doesn't exist
        'مصادر التمويل المحتملة': 'funding_sources'
    }
    
    # Write data rows with white background
    for row_num, project in enumerate(queryset, 1):
        # Use data_style (white background) for all rows
        row_style = data_style
        
        for col_num, arabic_header in enumerate(arabic_headers):
            field_name = field_map.get(arabic_header, '')
            if field_name:
                # Get the value from the project instance
                value = getattr(project, field_name, '')
                
                # Format the value for display
                if value is None:
                    value = ''
                elif isinstance(value, (list, dict)):
                    value = ', '.join(map(str, value)) if isinstance(value, list) else str(value)
                elif hasattr(value, 'all'):  # Handle ManyToMany fields
                    value = ', '.join(str(item) for item in value.all())
                
                # Format dates if needed
                if hasattr(value, 'strftime'):
                    value = value.strftime('%Y-%m-%d')
                
                # Format numbers if needed
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if field_name in ['estimated_cost', 'property_prep_cost']:
                        value = f"{value:,.2f}"
                
                # Write the cell with appropriate style
                ws.write(row_num, col_num, str(value), row_style)
        
        # Set row height to auto-adjust to content
        ws.row(row_num).height_mismatch = True
        ws.row(row_num).height = 256  # Default height, will expand with wrapped text
    
    wb.save(response)
    return response
