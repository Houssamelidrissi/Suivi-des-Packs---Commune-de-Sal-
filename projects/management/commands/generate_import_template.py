from django.core.management.base import BaseCommand
import os
from django.conf import settings
import tablib
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generates a sample Excel template for importing projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='project_import_template.xlsx',
            help='Output file name (default: project_import_template.xlsx)'
        )

    def handle(self, *args, **options):
        # Define the headers with Arabic labels
        headers = [
            'code',                  # الرمز
            'program',               # البرنامج
            'projects',              # المشاريع
            'location',              # المكان
            'district',              # المقاطعة/الجماعة
            'planning_code',         # الرمز في تصميم التهيئة
            'development_goals',     # الأهداف التنموية
            'components',            # مكونات المشروع
            'target_group',          # الفئة المستهدفة
            'project_goals',         # أهداف المشروع
            'property_status',       # وضعية العقار
            'property_drawing',      # الرسم العقاري
            'area',                  # المساحة (متر مربع)
            'property_prep_cost',    # كلفة تعبئة العقار (درهم)
            'studies',               # الدراسات
            'achievements',          # الإنجازات
            'estimated_cost',        # التكلفة التقديرية (درهم)
            'start_year',            # سنة الانطلاق
            'estimated_duration',    # المدة التقديرية (أشهر)
            'implementation_years',  # سنوات التنفيذ (سنوات مفصولة بفاصلة)
            'budget_years',         # سنوات الميزانية (سنوات مفصولة بفاصلة)
            'indicator_1',          # المؤشر 1
            'indicator_2',          # المؤشر 2
            'indicator_3',          # المؤشر 3
            'potential_partners',    # الشركاء المحتملين
            'funding_sources',       # مصادر التمويل المحتملة
        ]

        # Create sample data with some default values
        data = [
            [
                '',  # code (will be auto-generated if empty)
                'برنامج التنمية المحلية',  # program
                'مشروع نموذجي',  # projects
                'الرباط',  # location
                'أكدال',  # district
                'PLAN-001',  # planning_code
                'تحسين البنية التحتية',  # development_goals
                'بناء وتجهيز',  # components
                'السكان المحليون',  # target_group
                'تحسين جودة الحياة',  # project_goals
                'ملكية عمومية',  # property_status
                'R-2023-001',  # property_drawing
                '1000.00',  # area
                '50000.00',  # property_prep_cost
                'دراسات الجدوى',  # studies
                'تم إنجاز 50%',  # achievements
                '1000000.00',  # estimated_cost
                '2025',  # start_year
                '12',  # estimated_duration
                '2025,2026',  # implementation_years
                '2025,2026',  # budget_years
                'مؤشر الأداء 1',  # indicator_1
                'مؤشر الأداء 2',  # indicator_2
                'مؤشر الأداء 3',  # indicator_3
                'الوزارة المكلفة بالإسكان',  # potential_partners
                'الميزانية العامة للدولة',  # funding_sources
            ],
            # Add a second row with different values
            [
                'CUSTOM-CODE-001',  # code
                'برنامج التنمية القروية',  # program
                'مشروع تنموي',  # projects
                'مراكش',  # location
                'سيدي يوسف بن علي',  # district
                'PLAN-002',  # planning_code
                'تعزيز البنية التحتية الريفية',  # development_goals
                'تعبيد الطرق',  # components
                'سكان العالم القروي',  # target_group
                'تحسين التنقل',  # project_goals
                'ملكية جماعية',  # property_status
                'R-2023-002',  # property_drawing
                '2000.50',  # area
                '75000.00',  # property_prep_cost
                'دراسات تقنية',  # studies
                'في طور الإنجاز',  # achievements
                '2500000.00',  # estimated_cost
                '2024',  # start_year
                '18',  # estimated_duration
                '2024,2025,2026',  # implementation_years
                '2024,2025',  # budget_years
                'مؤشر التنقل',  # indicator_1
                'مؤشر الرضا',  # indicator_2
                'مؤشر الجودة',  # indicator_3
                'المجلس الإقليمي',  # potential_partners
                'صندوق التنمية القروية',  # funding_sources
            ]
        ]

        # Create a dataset
        dataset = tablib.Dataset(*data, headers=headers)

        # Get the output file path
        output_file = options['output']
        if not output_file.endswith(('.xls', '.xlsx')):
            output_file += '.xlsx'
        
        output_path = os.path.join(settings.BASE_DIR, output_file)

        # Write to Excel file
        with open(output_path, 'wb') as f:
            f.write(dataset.export('xlsx'))

        self.stdout.write(
            self.style.SUCCESS(f'تم إنشاء ملف النموذج بنجاح: {output_path}')
        )
        self.stdout.write(
            self.style.WARNING('ملاحظة: يمكنك حذف أي أعمدة غير مطلوبة من الملف')
        )
