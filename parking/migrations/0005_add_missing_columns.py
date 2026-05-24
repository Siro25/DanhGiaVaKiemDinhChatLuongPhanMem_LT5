# Add missing columns to parking_parkinglot table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0004_create_parkinglot_table'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE `parking_parkinglot`
            ADD COLUMN `description` longtext,
            ADD COLUMN `location` varchar(200) NOT NULL DEFAULT '',
            ADD COLUMN `status` varchar(20) NOT NULL DEFAULT 'active',
            ADD COLUMN `hourly_rate` decimal(10,2) NOT NULL DEFAULT '0.00',
            ADD COLUMN `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            ADD COLUMN `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6);
            """,
            reverse_sql="SELECT 1;"  # Cannot easily reverse ALTER TABLE ADD COLUMN
        ),
    ]
