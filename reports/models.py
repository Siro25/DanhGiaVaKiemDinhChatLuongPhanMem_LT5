from django.db import models
from django.utils.translation import gettext_lazy as _

class Report(models.Model):
    """
    Model quản lý báo cáo thống kê
    """
    REPORT_TYPE_CHOICES = (
        ('daily', 'Báo cáo ngày'),
        ('monthly', 'Báo cáo tháng'),
    )
    
    title = models.CharField(_('Tiêu đề'), max_length=200)
    report_type = models.CharField(_('Loại báo cáo'), max_length=20, choices=REPORT_TYPE_CHOICES)
    report_date = models.DateField(_('Ngày báo cáo'))
    content = models.TextField(_('Nội dung'))
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Báo cáo')
        verbose_name_plural = _('Báo cáo')
    
    def __str__(self):
        return f"{self.title} - {self.report_date}"