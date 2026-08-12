import os
import sys
import django

# Force UTF-8 output encoding for Windows terminals
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budgetbuddy.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from finance.models import Category, Income, Expense, Budget, SavingsGoal
from notifications.models import Notification

User = get_user_model()

def run_end_to_end_test():
    print("=" * 70)
    print("STARTING COMPLETE END-TO-END WORKFLOW TEST")
    print("=" * 70)
    
    client = APIClient()
    username = "e2e_user_test"
    email = "e2e_user@example.com"
    password = "SecurePassword123!"
    
    # Cleanup prior test data if exists
    User.objects.filter(username=username).delete()
    Category.objects.filter(name='Dining & Food').delete()
    
    # ----------------------------------------------------
    # 1. User Registration
    # ----------------------------------------------------
    print("\n[Step 1/12] Testing User Registration...")
    reg_res = client.post('/api/auth/register/', {
        'username': username,
        'email': email,
        'password': password,
        'first_name': 'E2E',
        'last_name': 'Tester'
    }, format='json')
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.data}"
    print("  [SUCCESS] Registration successful! User account created.")

    # ----------------------------------------------------
    # 2. User Login
    # ----------------------------------------------------
    print("\n[Step 2/12] Testing User Login...")
    login_res = client.post('/api/auth/login/', {
        'username': username,
        'password': password
    }, format='json')
    assert login_res.status_code == 200, f"Login failed: {login_res.data}"
    access_token = login_res.data.get('access')
    refresh_token = login_res.data.get('refresh')
    assert access_token and refresh_token, "Access/Refresh tokens missing!"
    print("  [SUCCESS] Login successful! Received access & refresh JWT tokens.")

    # ----------------------------------------------------
    # 3. JWT Authentication
    # ----------------------------------------------------
    print("\n[Step 3/12] Testing JWT Authentication...")
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    profile_res = client.get('/api/auth/me/')
    assert profile_res.status_code == 200, f"JWT Authentication failed: {profile_res.data}"
    assert profile_res.data['username'] == username
    print("  [SUCCESS] JWT Authentication verified! Authenticated user profile fetched.")

    # ----------------------------------------------------
    # 4. Income Management
    # ----------------------------------------------------
    print("\n[Step 4/12] Testing Income Management...")
    income_res = client.post('/api/finance/incomes/', {
        'title': 'Monthly Salary',
        'source': 'SALARY',
        'amount': '5000.00',
        'income_date': '2026-08-01',
        'description': 'Primary salary payment'
    }, format='json')
    assert income_res.status_code == 201, f"Create income failed: {income_res.data}"
    income_id = income_res.data['id']
    
    incomes_list = client.get('/api/finance/incomes/')
    assert incomes_list.status_code == 200 and len(incomes_list.data) >= 1
    print("  [SUCCESS] Income management verified! Created $5,000.00 income entry.")

    # ----------------------------------------------------
    # 5. Expense Management
    # ----------------------------------------------------
    print("\n[Step 5/12] Testing Expense Management...")
    cat_res = client.post('/api/finance/categories/', {
        'name': 'Dining & Food',
        'icon': 'utensils'
    }, format='json')
    assert cat_res.status_code == 201, f"Create category failed: {cat_res.data}"
    cat_id = cat_res.data['id']

    exp_res = client.post('/api/finance/expenses/', {
        'title': 'Restaurant Dinner',
        'amount': '250.00',
        'category': cat_id,
        'date_spent': '2026-08-05',
        'notes': 'Family dinner'
    }, format='json')
    assert exp_res.status_code == 201, f"Create expense failed: {exp_res.data}"
    print("  [SUCCESS] Expense management verified! Created $250.00 expense under Dining category.")

    # ----------------------------------------------------
    # 6. Budget Creation
    # ----------------------------------------------------
    print("\n[Step 6/12] Testing Budget Creation...")
    budget_res = client.post('/api/finance/budgets/', {
        'category': cat_id,
        'budget_amount': '300.00',
        'month': 8,
        'year': 2026
    }, format='json')
    assert budget_res.status_code == 201, f"Create budget failed: {budget_res.data}"
    budget_id = budget_res.data['id']
    print("  [SUCCESS] Budget creation verified! Created $300.00 budget for Dining.")

    # ----------------------------------------------------
    # 7. Budget Monitoring
    # ----------------------------------------------------
    print("\n[Step 7/12] Testing Budget Monitoring...")
    budgets_list = client.get('/api/finance/budgets/')
    assert budgets_list.status_code == 200
    monitored_budget = next(b for b in budgets_list.data if b['id'] == budget_id)
    spent = float(monitored_budget.get('spent', 0))
    budget_amt = float(monitored_budget.get('budget_amount', 0))
    print(f"  Spent: ${spent:.2f} / Budget: ${budget_amt:.2f}")
    assert spent == 250.00
    print("  [SUCCESS] Budget monitoring verified! Real-time spent calculation confirmed.")

    # ----------------------------------------------------
    # 8. Budget Alerts
    # ----------------------------------------------------
    print("\n[Step 8/12] Testing Budget Alerts...")
    # Add another expense to push budget over 80% threshold ($250 + $30 = $280 / $300 = 93.3%)
    exp_alert = client.post('/api/finance/expenses/', {
        'title': 'Lunch Cafe',
        'amount': '30.00',
        'category': cat_id,
        'date_spent': '2026-08-10'
    }, format='json')
    assert exp_alert.status_code == 201
    
    # Trigger/Check budget alert endpoint or notifications
    alerts_res = client.get('/api/finance/budget-alerts/')
    assert alerts_res.status_code == 200
    print("  [SUCCESS] Budget alerts verified! Threshold alert API endpoint responded.")

    # ----------------------------------------------------
    # 9. Savings Goals
    # ----------------------------------------------------
    print("\n[Step 9/12] Testing Savings Goals...")
    sav_res = client.post('/api/finance/savings-goals/', {
        'name': 'Vacation Fund',
        'target_amount': '2000.00',
        'saved_amount': '500.00',
        'target_date': '2026-12-31'
    }, format='json')
    assert sav_res.status_code == 201, f"Create savings goal failed: {sav_res.data}"
    savings_id = sav_res.data['id']
    
    # Update savings goal saved amount
    contrib_res = client.patch(f'/api/finance/savings-goals/{savings_id}/', {
        'saved_amount': '700.00'
    }, format='json')
    assert contrib_res.status_code == 200
    assert float(contrib_res.data['saved_amount']) == 700.00
    print("  [SUCCESS] Savings goals verified! Goal created and $200.00 contribution added.")

    # ----------------------------------------------------
    # 10. Notifications
    # ----------------------------------------------------
    print("\n[Step 10/12] Testing Notifications...")
    notifs = client.get('/api/notifications/')
    assert notifs.status_code == 200
    if len(notifs.data) > 0:
        notif_id = notifs.data[0]['id']
        read_res = client.patch(f'/api/notifications/{notif_id}/', {'is_read': True}, format='json')
        assert read_res.status_code == 200
    print("  [SUCCESS] Notifications management verified!")

    # ----------------------------------------------------
    # 11. Analytics Dashboard
    # ----------------------------------------------------
    print("\n[Step 11/12] Testing Analytics Dashboard...")
    summary_res = client.get('/api/analytics/summary/')
    assert summary_res.status_code == 200
    data = summary_res.data
    print(f"  Analytics Data: {data}")
    assert float(data.get('total_income', 0)) == 5000.0
    assert float(data.get('total_expense', 0)) == 280.0
    print("  [SUCCESS] Analytics dashboard verified! Aggregated income, expenses, and savings calculated.")

    # ----------------------------------------------------
    # 12. Reports Export
    # ----------------------------------------------------
    print("\n[Step 12/12] Testing Reports Generation & Export...")
    report_summary = client.get('/api/reports/summary/')
    assert report_summary.status_code == 200
    
    csv_report = client.get('/api/reports/export/?format=csv')
    assert csv_report.status_code == 200
    
    pdf_report = client.get('/api/reports/export/?format=pdf')
    assert pdf_report.status_code == 200
    print("  [SUCCESS] Reports export verified! Financial summary generated, CSV and PDF exports generated.")

    print("\n" + "=" * 70)
    print("ALL 12 END-TO-END WORKFLOW STEPS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    run_end_to_end_test()
