import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

settings_file = os.path.join(backend_dir, 'budgetbuddy', 'settings.py')
with open(settings_file, 'r', encoding='utf-8') as f:
    code = compile(f.read(), settings_file, 'exec')
    exec(code, globals())
