import os
import sys

# Ensure backend directory is first in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budgetbuddy.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
