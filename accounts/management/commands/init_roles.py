from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User


class Command(BaseCommand):
    help = 'Khởi tạo nhóm quyền: admin và staff'

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name='admin')
        staff_group, _ = Group.objects.get_or_create(name='staff')

        # Admin: toàn quyền
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)

        # Staff: chỉ quyền xem cho tất cả models
        view_perms = Permission.objects.filter(codename__startswith='view_')
        staff_group.permissions.set(view_perms)

        self.stdout.write(self.style.SUCCESS('Đã khởi tạo nhóm và phân quyền mặc định.'))


