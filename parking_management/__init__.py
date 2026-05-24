from django.db import migrations, models
import pymysql
pymysql.install_as_MySQLdb()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', 'XXXX_previous_migration'),  # Thay bằng migration trước đó
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False, verbose_name='Đã xác thực'),
        ),
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Chờ xác thực'), ('approved', 'Đã xác thực'), ('rejected', 'Từ chối')],
                default='approved',
                max_length=20,
                verbose_name='Trạng thái'
            ),
        ),
    ]

