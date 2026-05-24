from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_alter_customer_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_customers', to=settings.AUTH_USER_MODEL, verbose_name='Nhân viên phụ trách'),
        ),
        migrations.AddField(
            model_name='customer',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='Ghi chú'),
        ),
        migrations.AddField(
            model_name='customer',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Hoạt động'),
        ),
    ]
