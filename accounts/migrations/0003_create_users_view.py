from django.db import migrations


VIEW_SQL = r'''
CREATE OR REPLACE VIEW users AS
SELECT
    au.id AS id,
    au.username AS username,
    au.password AS password_hash,
    au.full_name AS full_name,
    CASE WHEN au.role = 'admin' THEN 'admin' ELSE 'nhanvien' END AS role,
    au.date_joined AS created_at
FROM accounts_user au;
'''


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_user_full_name_alter_user_role'),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL,
            reverse_sql="DROP VIEW IF EXISTS users;",
        )
    ]


