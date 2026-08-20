import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

urls_file = os.path.join(backend_dir, 'budgetbuddy', 'urls.py')
with open(urls_file, 'r', encoding='utf-8') as f:
    code = compile(f.read(), urls_file, 'exec')
    exec(code, globals())
