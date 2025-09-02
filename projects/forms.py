from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Project, ExecutionRate


class ProjectImportForm(forms.Form):
    """Form for importing projects from Excel file."""
    file = forms.FileField(
        label=_('ملف Excel'),
        help_text=_('يرجى تحميل ملف Excel يحتوي على بيانات المشاريع'),
        widget=forms.FileInput(attrs={
            'accept': '.xlsx, .xls',
            'class': 'form-control',
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.endswith(('.xls', '.xlsx')):
                raise forms.ValidationError(_('الرجاء تحميل ملف Excel صالح (ملفات xls أو xlsx فقط)'))
            
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if file.size > max_size:
                raise forms.ValidationError(_('حجم الملف كبير جداً. الحد الأقصى المسموح به هو 5 ميجابايت'))
            
            # Check file content type
            valid_content_types = [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/octet-stream',  # Some Excel files might have this
            ]
            if file.content_type not in valid_content_types:
                raise forms.ValidationError(_('نوع الملف غير صالح. يرجى تحميل ملف Excel'))
            
        return file

class CheckboxSelectMultipleRTL(forms.CheckboxSelectMultiple):
    template_name = 'projects/widgets/checkbox_select_rtl.html'
    option_template_name = 'projects/widgets/checkbox_option_rtl.html'

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up the year fields with checkboxes
        year_choices = [
            ('2022', '2022'),
            ('2023', '2023'),
            ('2024', '2024'),
            ('2025', '2025'),
            ('2026', '2026'),
            ('2027', '2027'),
            ('2028', '2028'),
        ]
        
        self.fields['implementation_years'] = forms.MultipleChoiceField(
            label=_('سنوات التنفيذ'),
            choices=year_choices,
            widget=CheckboxSelectMultipleRTL(),
            required=True
        )
        
        self.fields['budget_years'] = forms.MultipleChoiceField(
            label=_('سنوات الميزانية'),
            choices=year_choices,
            widget=CheckboxSelectMultipleRTL(),
            required=True
        )
        
        # Configure estimated_cost field
        self.fields['estimated_cost'].widget.attrs.update({
            'class': 'form-control text-right',
            'step': '0.01',
            'min': '0',
            'dir': 'ltr',  # Keep numbers LTR even in RTL context
        })
        
        # Configure estimated_duration field to only accept integers
        self.fields['estimated_duration'].widget.attrs.update({
            'class': 'form-control text-right',
            'step': '1',
            'min': '1',
            'type': 'number',
            'dir': 'ltr',  # Keep numbers LTR even in RTL context
        })
        
        # Set initial values from the model instance if editing
        if self.instance and self.instance.pk:
            self.fields['implementation_years'].initial = self.instance.implementation_years or []
            self.fields['budget_years'].initial = self.instance.budget_years or []
            
            # Set initial estimated_cost to the calculated total if not set
            if not self.instance.estimated_cost:
                self.initial['estimated_cost'] = self.instance.total_estimated_cost
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            # Skip if this is one of our custom fields
            if field_name in ['implementation_years', 'budget_years', 'estimated_cost']:
                continue
                
            # Initialize attrs if it doesn't exist
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
                
            # Add form-control class for standard fields
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
            
            # Add RTL and text-right for Arabic text input
            if field_name in ['program', 'projects', 'location', 'district', 'components', 
                            'target_group', 'property_status', 'studies', 'achievements',
                            'potential_partners', 'funding_sources', 'indicator_1', 
                            'indicator_2', 'indicator_3']:
                field.widget.attrs['dir'] = 'rtl'
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' text-right'
                else:
                    field.widget.attrs['class'] = 'text-right'
            
            # Make required fields more obvious
            if field.required and 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' required'
    
    def clean(self):
        cleaned_data = super().clean()
        planned_end_date = cleaned_data.get('planned_end_date')
        actual_end_date = cleaned_data.get('actual_end_date')
        
        # Only validate if both dates are provided
        if planned_end_date and actual_end_date and actual_end_date < planned_end_date:
            self.add_error('actual_end_date', 
                         _('يجب أن يكون تاريخ الانتهاء الفعلي بعد التاريخ المخطط للانتهاء'))
        
        return cleaned_data
    
    def save(self, commit=True):
        # Save the form data
        instance = super().save(commit=False)
        
        # Save the selected years as lists
        if 'implementation_years' in self.cleaned_data:
            instance.implementation_years = self.cleaned_data['implementation_years']
        if 'budget_years' in self.cleaned_data:
            instance.budget_years = self.cleaned_data['budget_years']
        
        if commit:
            instance.save()
        
        return instance


class ExecutionRateForm(forms.ModelForm):
    class Meta:
        model = ExecutionRate
        fields = [
            'project', 'programmed_amount', 'partner_contribution',
            'programming_date', 'market_launch_date', 'actual_costs',
            'estimated_costs', 'expected_end_date', 'actual_start_date',
            'actual_end_date', 'work_progress_percentage',
            'financial_achievement_percentage'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'programming_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'market_launch_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'actual_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'actual_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up the project field to show code and program
        self.fields['project'].label_from_instance = lambda obj: f"{obj.code} - {obj.program}"
        
        # Add Bootstrap classes and other attributes to form fields
        for field_name, field in self.fields.items():
            # Initialize attrs if it doesn't exist
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
                
            # Add form-control class for standard fields
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            
            # Add RTL and text-right for Arabic text input
            if field_name in ['project']:
                field.widget.attrs['dir'] = 'rtl'
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' text-right'
                else:
                    field.widget.attrs['class'] = 'text-right'
            
            # Configure numeric fields
            if field_name in ['programmed_amount', 'partner_contribution', 'actual_costs', 
                            'estimated_costs', 'work_progress_percentage', 'financial_achievement_percentage']:
                field.widget.attrs.update({
                    'step': '0.01',
                    'min': '0',
                    'dir': 'ltr',
                    'class': 'form-control text-end'
                })
                
                # Add percentage sign for percentage fields
                if field_name in ['work_progress_percentage', 'financial_achievement_percentage']:
                    field.widget.attrs.update({
                        'max': '100',
                        'step': '0.1',
                        'placeholder': '0.00 %',
                        'class': 'form-control text-end percentage-input'
                    })
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Get all date fields
        actual_start_date = cleaned_data.get('actual_start_date')
        actual_end_date = cleaned_data.get('actual_end_date')
        expected_end_date = cleaned_data.get('expected_end_date')
        
        # Only validate actual_end_date if both dates are provided
        if actual_start_date and actual_end_date and actual_end_date < actual_start_date:
            self.add_error('actual_end_date', 
                         _('يجب أن يكون تاريخ الانتهاء الفعلي بعد تاريخ البداية الفعلية'))
        
        # Make cost validation less strict
        actual_costs = cleaned_data.get('actual_costs')
        estimated_costs = cleaned_data.get('estimated_costs')
        
        if actual_costs is not None and estimated_costs is not None and estimated_costs > 0:
            from decimal import Decimal
            max_allowed = Decimal(str(estimated_costs)) * Decimal('10.0')  # Allow up to 10x overrun
            if actual_costs > max_allowed:
                self.add_error('actual_costs',
                             _('التكاليف الفعلية أعلى من التقديرية بنسبة كبيرة. يرجى مراجعة القيم'))
        
        return cleaned_data
