from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator

class Project(models.Model):
    # Basic Information
    code = models.CharField(_('الرمز'), max_length=100, unique=True)
    program = models.CharField(_('البرنامج'), max_length=255)
    projects = models.TextField(_('المشاريع'))
    location = models.CharField(_('المكان'), max_length=255)
    district = models.CharField(_('المقاطعة/الجماعة'), max_length=255)
    planning_code = models.CharField(_('الرمز في تصميم التهيئة'), max_length=100, blank=True, null=True)
    development_goals = models.TextField(_('الأهداف التنموية'), blank=True, null=True, help_text=_('أدخل الأهداف التنموية للمشروع'))
    
    # Project Details
    components = models.TextField(_('مكونات المشروع'))
    target_group = models.TextField(_('الفئة المستهدفة'))
    project_goals = models.TextField(_('أهداف المشروع'), blank=True, null=True, help_text=_('أدخل الأهداف الرئيسية للمشروع'))
    property_status = models.CharField(_('وضعية العقار'), max_length=100)
    property_drawing = models.CharField(_('الرسم العقاري'), max_length=100, blank=True, null=True)
    area = models.DecimalField(_('المساحة'), max_digits=10, decimal_places=2, help_text=_('بالمتر المربع'))
    property_prep_cost = models.DecimalField(_('كلفة تعبئة العقار'), max_digits=15, decimal_places=2, 
                                           help_text=_('بالدرهم المغربي'))
    
    # Studies and Implementation
    studies = models.TextField(_('الدراسات'), blank=True, null=True)
    achievements = models.TextField(_('الإنجازات'), blank=True, null=True)
    estimated_cost = models.DecimalField(_('التكلفة التقديرية'), max_digits=15, decimal_places=2,
                                       help_text=_('بالدرهم المغربي'))
    start_year = models.PositiveIntegerField(_('سنة الانطلاق'))
    estimated_duration = models.PositiveIntegerField(_('المدة التقديرية (أشهر)'))
    
    # Budget and Indicators
    YEAR_CHOICES = [
        ('2022', '2022'),
        ('2023', '2023'),
        ('2024', '2024'),
        ('2025', '2025'),
        ('2026', '2026'),
        ('2027', '2027'),
        ('2028', '2028'),
    ]
    implementation_years = models.JSONField(_('سنوات التنفيذ'), default=list, help_text=_('اختر سنوات التنفيذ'))
    budget_years = models.JSONField(_('سنوات الميزانية'), default=list, help_text=_('اختر سنوات الميزانية'))
    indicator_1 = models.CharField(_('المؤشر 1'), max_length=255, blank=True, null=True)
    indicator_2 = models.CharField(_('المؤشر 2'), max_length=255, blank=True, null=True)
    indicator_3 = models.CharField(_('المؤشر 3'), max_length=255, blank=True, null=True)
    
    # Partners and Funding
    potential_partners = models.TextField(_('الشركاء المحتملين'), blank=True, null=True)
    funding_sources = models.TextField(_('مصادر التمويل المحتملة'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('مشروع')
        verbose_name_plural = _('المشاريع')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.program}"
        
    @property
    def total_estimated_cost(self):
        """
        Calculate the total estimated cost as the sum of:
        - studies (converted to float, default to 0)
        - achievements (converted to float, default to 0)
        - property_prep_cost (already a Decimal)
        """
        total = self.property_prep_cost or 0
        
        try:
            studies_cost = float(self.studies) if self.studies and self.studies.strip() else 0
            total += studies_cost
        except (ValueError, TypeError):
            pass
            
        try:
            achievements_cost = float(self.achievements) if self.achievements and self.achievements.strip() else 0
            total += achievements_cost
        except (ValueError, TypeError):
            pass
            
        return total
        
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'pk': self.pk})


class ProjectTracking(models.Model):
    """Model to track project progress and financial information."""
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='tracking',
        verbose_name=_('المشروع')
    )
    
    # Basic info (linked from Project)
    # code = from Project.code
    # project_name = from Project.program
    # estimated_cost = from Project.estimated_cost
    # potential_partners = from Project.potential_partners
    # start_year = from Project.start_year
    
    # New fields for tracking
    market_launch_date = models.DateField(
        _('تاريخ إطلاق السوق'),
        null=True,
        blank=True
    )
    
    actual_costs = models.DecimalField(
        _('التكاليف الفعلية'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('بالدرهم المغربي')
    )
    
    planned_end_date = models.DateField(
        _('تاريخ الانتهاء المخطط'),
        null=True,
        blank=True
    )
    
    actual_start_date = models.DateField(
        _('تاريخ البدء الفعلي'),
        null=True,
        blank=True
    )
    
    actual_end_date = models.DateField(
        _('تاريخ الانتهاء الفعلي'),
        null=True,
        blank=True
    )
    
    # Auto-calculated fields
    cost_variance_percentage = models.DecimalField(
        _('الفرق في التكلفة (%)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False
    )
    
    delay_rate = models.DecimalField(
        _('معدل التأخير'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False
    )
    
    delay_variance_days = models.IntegerField(
        _('الفرق في الأيام'),
        null=True,
        blank=True,
        editable=False
    )
    
    class Meta:
        verbose_name = _('تتبع المشروع')
        verbose_name_plural = _('')
    
    def __str__(self):
        return f"تتبع - {self.project.code} - {self.project.program}"
    
    def calculate_cost_variance(self):
        """
        Calculate the cost variance percentage between estimated and actual costs.
        Formula: ((Estimated Cost - Actual Cost) / Estimated Cost) * 100
        
        Returns:
            Decimal or None: The cost variance percentage or None if calculation is not possible
        """
        if self.actual_costs is not None and self.project.estimated_cost:
            try:
                return (
                    (self.project.estimated_cost - self.actual_costs) / 
                    self.project.estimated_cost * 100
                )
            except (TypeError, ZeroDivisionError):
                return None
        return None
    
    def calculate_delay_metrics(self):
        """
        Calculate delay-related metrics including delay rate and variance in days.
        
        Returns:
            tuple: (delay_rate, delay_variance_days) or (None, None) if calculation is not possible
        """
        if not all([self.planned_end_date, self.actual_end_date, self.actual_start_date]):
            return None, None
            
        try:
            # Ensure we have date objects
            planned_end = self.planned_end_date
            actual_end = self.actual_end_date
            actual_start = self.actual_start_date
            
            # Calculate total planned duration in days
            total_planned_days = (planned_end - actual_start).days
            if total_planned_days <= 0:
                return None, None
                
            # Calculate actual duration in days
            actual_duration = (actual_end - actual_start).days
            if actual_duration <= 0:
                return None, None
                
            # Calculate delay variance in days
            delay_days = (actual_end - planned_end).days
            
            # Calculate delay rate (percentage of delay relative to planned duration)
            delay_rate = (delay_days / total_planned_days) * 100
            
            return delay_rate, delay_days
            
        except (TypeError, AttributeError, ValueError) as e:
            print(f"Error calculating delay metrics: {e}")
            return None, None
    
    def save(self, *args, **kwargs):
        """
        Override save method to calculate and update metrics before saving.
        """
        # Calculate cost variance percentage
        self.cost_variance_percentage = self.calculate_cost_variance()
        
        # Calculate delay metrics
        self.delay_rate, self.delay_variance_days = self.calculate_delay_metrics()
        
        # Call the parent's save method
        super().save(*args, **kwargs)
        
        # Update related project if needed
        self._update_project_status()
    
    def _update_project_status(self):
        """
        Update related project status based on tracking information.
        This can be expanded to update project status based on tracking data.
        """
        # Example: You could update project status based on completion
        if self.actual_end_date and not self.project.achievements:
            self.project.achievements = _("تم الانتهاء من المشروع في {}").format(
                self.actual_end_date.strftime('%Y-%m-%d')
            )
            self.project.save(update_fields=['achievements'])
    
    @property
    def is_delayed(self):
        """
        Check if the project is delayed.
        
        Returns:
            bool: True if the project is delayed, False otherwise
        """
        if self.planned_end_date and self.actual_end_date:
            return self.actual_end_date > self.planned_end_date
        return False
    
    @property
    def status_display(self):
        """
        Get a human-readable status of the project tracking.
        
        Returns:
            str: Status description in Arabic
        """
        if not self.actual_start_date:
            return _("لم يبدأ بعد")
        elif not self.actual_end_date:
            return _("قيد التنفيذ")
        elif self.is_delayed and self.delay_variance_days is not None:
            return _("متأخر - {} يوم").format(abs(self.delay_variance_days))
        else:
            return _("مكتمل في الوقت المحدد")
    
    def get_absolute_url(self):
        return reverse('project_tracking_detail', kwargs={'pk': self.pk})


class ExecutionRate(models.Model):
    """Model to track project execution rate and financial metrics."""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='execution_rates',
        verbose_name=_('المشروع')
    )
    
    # Basic Information
    programmed_amount = models.DecimalField(
        _('المبلغ المبرمج'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('بالدرهم المغربي')
    )
    
    partner_contribution = models.DecimalField(
        _('تعبئة الشركاء'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('بالدرهم المغربي')
    )
    
    programming_date = models.DateField(
        _('تاريخ البرمجة'),
        null=True,
        blank=True
    )
    
    market_launch_date = models.DateField(
        _('تاريخ إطلاق الصفقات'),
        null=True,
        blank=True
    )
    
    # Cost Information
    actual_costs = models.DecimalField(
        _('التكاليف الفعلية (أ)'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('بالدرهم المغربي')
    )
    
    estimated_costs = models.DecimalField(
        _('التكاليف التقديرية (ب)'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('بالدرهم المغربي')
    )
    
    cost_difference_percentage = models.DecimalField(
        _('فرق التكلفة (%)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False
    )
    
    # Schedule Information
    expected_end_date = models.DateField(
        _('تاريخ الانتهاء المتوقع'),
        null=True,
        blank=True
    )
    
    actual_start_date = models.DateField(
        _('تاريخ البداية الفعلية'),
        null=True,
        blank=True
    )
    
    actual_end_date = models.DateField(
        _('تاريخ الانتهاء الفعلي'),
        null=True,
        blank=True
    )
    
    # Calculated Fields
    delay_percentage = models.DecimalField(
        _('معدل التأخير (%)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False
    )
    
    duration_difference_days = models.IntegerField(
        _('فرق المدة (بالأيام)'),
        null=True,
        blank=True,
        editable=False
    )
    
    work_progress_percentage = models.DecimalField(
        _('معدل التقدم (%) للأشغال'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    financial_achievement_percentage = models.DecimalField(
        _('معدل الإنجاز (%) (مالي)'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('معدل التنفيذ')
        verbose_name_plural = _('معدلات التنفيذ')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project.code} - {self.project.program} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # Calculate cost difference percentage if both actual and estimated costs exist
        if self.actual_costs is not None and self.estimated_costs and self.estimated_costs != 0:
            self.cost_difference_percentage = (
                (self.estimated_costs - self.actual_costs) / self.estimated_costs * 100
            )
        
        # Calculate delay percentage and duration difference if dates are available
        if self.expected_end_date and self.actual_end_date:
            delta = (self.actual_end_date - self.expected_end_date).days
            self.duration_difference_days = delta
            
            if self.expected_end_date and self.actual_start_date:
                total_days = (self.expected_end_date - self.actual_start_date).days
                if total_days > 0:
                    self.delay_percentage = (delta / total_days) * 100
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('execution_rate_detail', kwargs={'pk': self.pk})
