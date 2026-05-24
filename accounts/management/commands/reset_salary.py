from django.core.management.base import BaseCommand
from accounts.models import User, Salary

class Command(BaseCommand):
    help = 'Reset all employee salary and withdrawn to 0'

    def handle(self, *args, **options):
        # Reset tất cả lương và số đã rút về 0
        employees = User.objects.filter(role='nhanvien')
        
        reset_count = 0
        for employee in employees:
            salary, created = Salary.objects.get_or_create(
                user=employee,
                defaults={'basic_salary': 0, 'withdrawn': 0}
            )
            
            # Reset về 0
            salary.basic_salary = 0
            salary.withdrawn = 0
            salary.save()
            
            reset_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Reset salary for {employee.username}: basic_salary=0, withdrawn=0'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Successfully reset {reset_count} employee salaries to 0!'
            )
        )