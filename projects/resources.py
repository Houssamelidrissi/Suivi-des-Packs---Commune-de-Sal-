from import_export import resources, fields, widgets
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, Widget
from .models import Project
from django.utils.translation import gettext_lazy as _
import json

class EmptyStringToDefaultWidget(Widget):
    """Widget that converts empty strings to None."""
    def clean(self, value, row=None, *args, **kwargs):
        if value == '':
            return None
        return value

class JSONWidget(Widget):
    """Widget that handles JSON fields."""
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return []
        if isinstance(value, str):
            try:
                # Try to parse as JSON if it's a string
                return json.loads(value)
            except (ValueError, TypeError):
                # If it's not valid JSON, treat as a single value
                return [str(value)]
        elif isinstance(value, (list, tuple)):
            return list(value)
        return [str(value)]
    
    def render(self, value, obj=None):
        if not value:
            return ''
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

class ProjectResource(resources.ModelResource):
    # Explicitly define fields with proper column names and widgets
    code = fields.Field(column_name='الرمز', attribute='code')
    program = fields.Field(column_name='البرنامج', attribute='program')
    projects = fields.Field(column_name='المشاريع', attribute='projects')
    location = fields.Field(column_name='المكان', attribute='location')
    district = fields.Field(column_name='المقاطعة/الجماعة', attribute='district')
    planning_code = fields.Field(column_name='الرمز في تصميم التهيئة', attribute='planning_code')
    development_goals = fields.Field(column_name='الأهداف التنموية', attribute='development_goals')
    components = fields.Field(column_name='مكونات المشروع', attribute='components')
    target_group = fields.Field(column_name='الفئة المستهدفة', attribute='target_group')
    project_goals = fields.Field(column_name='أهداف المشروع', attribute='project_goals')
    property_status = fields.Field(column_name='وضعية العقار', attribute='property_status')
    property_drawing = fields.Field(column_name='الرسم العقاري', attribute='property_drawing')
    area = fields.Field(
        column_name='المساحة',
        attribute='area',
        widget=widgets.DecimalWidget()
    )
    property_prep_cost = fields.Field(
        column_name='كلفة تعبئة العقار',
        attribute='property_prep_cost',
        widget=widgets.DecimalWidget()
    )
    studies = fields.Field(column_name='الدراسات', attribute='studies')
    achievements = fields.Field(column_name='الإنجازات', attribute='achievements')
    estimated_cost = fields.Field(
        column_name='التكلفة التقديرية',
        attribute='estimated_cost',
        widget=widgets.DecimalWidget()
    )
    start_year = fields.Field(column_name='سنة الانطلاق', attribute='start_year')
    estimated_duration = fields.Field(column_name='المدة التقديرية (أشهر)', attribute='estimated_duration')
    
    # Add JSON fields to the resource with custom widget
    implementation_years = fields.Field(
        column_name='سنوات التنفيذ',
        attribute='implementation_years',
        widget=JSONWidget()
    )
    budget_years = fields.Field(
        column_name='سنوات الميزانية',
        attribute='budget_years',
        widget=JSONWidget()
    )
    
    class Meta:
        model = Project
        fields = [
            'code', 'program', 'projects', 'location', 'district', 'planning_code',
            'development_goals', 'components', 'target_group', 'project_goals',
            'property_status', 'property_drawing', 'area', 'property_prep_cost',
            'studies', 'achievements', 'estimated_cost', 'start_year', 'estimated_duration',
            'implementation_years', 'budget_years', 'indicator_1', 'indicator_2', 'indicator_3',
            'potential_partners', 'funding_sources'
        ]
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        import_id_fields = []
        force_init_instance = True
        
    def before_import_row(self, row, **kwargs):
        """Handle empty or invalid values before import."""
        from django.utils import timezone
        from random import randint
        from decimal import Decimal, InvalidOperation
        import re
        
        # Map Excel column names to field names
        field_mapping = {
            'الرمز': 'code',
            'البرنامج': 'program',
            'المشاريع': 'projects',
            'المكان': 'location',
            'المقاطعة/الجماعة': 'district',
            'الرمز في تصميم التهيئة': 'planning_code',
            'الأهداف التنموية': 'development_goals',
            'مكونات المشروع': 'components',
            'الفئة المستهدفة': 'target_group',
            'أهداف المشروع': 'project_goals',
            'وضعية العقار': 'property_status',
            'الرسم العقاري': 'property_drawing',
            'المساحة': 'area',
            'كلفة تعبئة العقار': 'property_prep_cost',
            'الدراسات': 'studies',
            'الإنجازات': 'achievements',
            'التكلفة التقديرية': 'estimated_cost',
            'سنة الانطلاق': 'start_year',
            'المدة التقديرية (أشهر)': 'estimated_duration'
        }
        
        # Create a new row with mapped field names
        mapped_row = {}
        for col_name, value in row.items():
            if col_name in field_mapping:
                mapped_row[field_mapping[col_name]] = value
            else:
                mapped_row[col_name] = value
        
        # Update the original row with mapped field names
        row.clear()
        row.update(mapped_row)
        
        # Clean and convert values
        for field_name, value in row.items():
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    value = None
                row[field_name] = value
        
        # Generate code if not provided
        if 'code' not in row or not row['code']:
            row['code'] = f"PRJ-{timezone.now().strftime('%Y%m%d')}-{randint(1000, 9999)}"
        
        # Handle numeric fields
        numeric_fields = {
            'area': '0.00',
            'property_prep_cost': '0.00',
            'estimated_cost': '0.00',
            'estimated_duration': '12',
            'start_year': str(timezone.now().year)
        }
        
        for field, default in numeric_fields.items():
            if field in row and row[field] is not None:
                try:
                    # Convert to string and clean
                    value = str(row[field]).strip()
                    # Remove any non-numeric characters except decimal point and negative sign
                    value = re.sub(r'[^\d.-]', '', value)
                    if value and value != '.':
                        # Convert to Decimal to handle both integers and floats
                        decimal_value = Decimal(value)
                        # Convert back to string with proper format
                        row[field] = str(decimal_value.normalize())
                    else:
                        row[field] = default
                except (ValueError, InvalidOperation, TypeError):
                    row[field] = default
        
        # Handle JSON fields
        json_fields = {
            'implementation_years': [],
            'budget_years': []
        }
        
        for field in json_fields.keys():
            if field in row and row[field]:
                try:
                    # If it's already a list, use it as is
                    if isinstance(row[field], list):
                        row[field] = [str(y) for y in row[field] if y]
                    # If it's a string that looks like a list, try to parse it
                    elif isinstance(row[field], str):
                        # Handle comma-separated values
                        if ',' in row[field]:
                            row[field] = [y.strip() for y in row[field].split(',') if y.strip()]
                        # Handle JSON string
                        elif row[field].startswith('[') and row[field].endswith(']'):
                            import json
                            row[field] = json.loads(row[field])
                        # Single value as a list
                        else:
                            row[field] = [row[field].strip()]
                except (ValueError, AttributeError):
                    row[field] = json_fields[field]
            else:
                row[field] = json_fields[field]
        
        # Set default values for required text fields if they're empty
        required_text_fields = {
            'program': 'برنامج غير محدد',
            'location': 'غير محدد',
            'district': 'غير محدد',
            'projects': 'مشروع جديد',
            'components': 'غير محدد',
            'target_group': 'غير محدد',
            'property_status': 'غير محدد',
        }
        
        for field, default in required_text_fields.items():
            if field not in row or not row[field] or str(row[field]).strip() == '':
                row[field] = default
        
    def get_export_headers(self, **kwargs):
        headers = []
        for field in self.get_export_fields():
            # Get the verbose_name from the model's _meta
            try:
                model_field = self.Meta.model._meta.get_field(field.column_name)
                headers.append(str(model_field.verbose_name))
            except:
                headers.append(field.column_name)
        return headers
        
    def before_save_instance(self, instance, using_transaction=True, dry_run=False, **kwargs):
        """Set default values before saving."""
        # Ensure required fields have values
        if not instance.area:
            instance.area = 0.00
        if not instance.property_prep_cost:
            instance.property_prep_cost = 0.00
        if not instance.estimated_cost:
            instance.estimated_cost = 0.00
        if not instance.start_year:
            instance.start_year = 2025
        if not instance.estimated_duration:
            instance.estimated_duration = 12
