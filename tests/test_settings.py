"""
Cấu hình Django test settings – dùng SQLite in-memory thay vì MySQL.

Mục đích:
  - Cho phép chạy whitebox tests mà không cần kết nối MySQL.
  - SQLite in-memory nhanh hơn và không yêu cầu setup server DB.

Cách dùng:
  python manage.py test tests.whitebox_tests --settings=tests.test_settings
"""

from parking_management.settings import *  # noqa: F401, F403

# Override database: dùng SQLite in-memory
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Tắt migration khi test để tăng tốc
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Đơn giản hóa password hashers để tăng tốc test
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Tắt logging trong test (tuỳ chọn)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}
