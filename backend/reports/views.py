import csv
import datetime
import io
from calendar import monthrange
from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report
from .serializers import (
    ReportSerializer, ExpenseReportItemSerializer,
    SavingsReportItemSerializer, CombinedFinancialSummarySerializer
)
from finance.models import Income, Expense, Budget, SavingsGoal
from notifications.models import Notification


def parse_date_range(request):
    """
    Task 6 — Add Date Filters:
    - Current Month (period=current_month)
    - Previous Month (period=previous_month)
    - Custom Start Date (start_date=2026-08-01)
    - Custom End Date (end_date=2026-08-31)
    - Month/Year (month=8&year=2026)
    """
    today = datetime.date.today()
    period = request.query_params.get('period')
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')
    month_str = request.query_params.get('month')
    year_str = request.query_params.get('year')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.date.fromisoformat(start_date_str)
            end_date = datetime.date.fromisoformat(end_date_str)
            return start_date, end_date
        except ValueError:
            pass

    if period == 'current_month':
        start_date = today.replace(day=1)
        _, last_day = monthrange(today.year, today.month)
        end_date = today.replace(day=last_day)
        return start_date, end_date

    if period == 'previous_month':
        first_of_this_month = today.replace(day=1)
        last_month_last_day = first_of_this_month - datetime.timedelta(days=1)
        start_date = last_month_last_day.replace(day=1)
        end_date = last_month_last_day
        return start_date, end_date

    if month_str and year_str:
        m = int(month_str)
        y = int(year_str)
        _, last_day = monthrange(y, m)
        start_date = datetime.date(y, m, 1)
        end_date = datetime.date(y, m, last_day)
        return start_date, end_date

    if month_str:
        m = int(month_str)
        y = today.year
        _, last_day = monthrange(y, m)
        start_date = datetime.date(y, m, 1)
        end_date = datetime.date(y, m, last_day)
        return start_date, end_date

    # Default date range: current month
    start_date = today.replace(day=1)
    _, last_day = monthrange(today.year, today.month)
    end_date = today.replace(day=last_day)
    return start_date, end_date


class ReportViewSet(viewsets.ModelViewSet):
    """CRUD API for Report model protected by JWT Authentication"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MonthlyFinancialReportView(APIView):
    """
    Task 2 — Create Monthly Financial Report API with Task 6 Date Filters
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_date, end_date = parse_date_range(request)

        total_income = Income.objects.filter(
            user=request.user,
            income_date__gte=start_date,
            income_date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_expense = Expense.objects.filter(
            user=request.user,
            date_spent__gte=start_date,
            date_spent__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        current_balance = total_income - total_expense

        total_savings = SavingsGoal.objects.filter(
            user=request.user
        ).aggregate(total=Sum('saved_amount'))['total'] or Decimal('0.00')

        budgets = Budget.objects.filter(
            user=request.user,
            month=start_date.month,
            year=start_date.year
        )
        total_budget = budgets.aggregate(total=Sum('budget_amount'))['total'] or Decimal('0.00')
        remaining_budget = total_budget - total_expense

        data = {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "month": start_date.month,
            "year": start_date.year,
            "total_income": f"{total_income:.2f}",
            "total_expense": f"{total_expense:.2f}",
            "current_balance": f"{current_balance:.2f}",
            "total_savings": f"{total_savings:.2f}",
            "remaining_budget": f"{remaining_budget:.2f}",
            "Total Income": f"{total_income:.2f}",
            "Total Expense": f"{total_expense:.2f}",
            "Current Balance": f"{current_balance:.2f}",
            "Total Savings": f"{total_savings:.2f}",
            "Remaining Budget": f"{remaining_budget:.2f}",
        }
        return Response(data, status=status.HTTP_200_OK)


class ExpenseReportView(APIView):
    """
    Task 3 — Create Expense Report API with Task 6 Date Filters
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_date, end_date = parse_date_range(request)

        expenses = Expense.objects.filter(
            user=request.user,
            date_spent__gte=start_date,
            date_spent__lte=end_date
        ).order_by('-date_spent')

        serializer = ExpenseReportItemSerializer(expenses, many=True)
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return Response({
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_expense": f"{total_expense:.2f}",
            "count": expenses.count(),
            "expenses": serializer.data,
            "records": serializer.data,
        }, status=status.HTTP_200_OK)


class SavingsReportView(APIView):
    """
    Task 4 — Create Savings Report API
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user)
        serializer = SavingsReportItemSerializer(goals, many=True)

        total_target = goals.aggregate(total=Sum('target_amount'))['total'] or Decimal('0.00')
        total_saved = goals.aggregate(total=Sum('saved_amount'))['total'] or Decimal('0.00')
        total_remaining = max(Decimal('0.00'), total_target - total_saved)

        if total_target > 0:
            overall_pct = float((total_saved / total_target) * Decimal('100.0'))
            overall_pct = round(min(100.0, max(0.0, overall_pct)), 2)
        else:
            overall_pct = 0.0

        return Response({
            "count": goals.count(),
            "total_target_amount": f"{total_target:.2f}",
            "total_saved_amount": f"{total_saved:.2f}",
            "total_remaining_amount": f"{total_remaining:.2f}",
            "overall_progress_percentage": overall_pct,
            "goals": serializer.data,
            "records": serializer.data,
        }, status=status.HTTP_200_OK)


class FinancialSummaryReportView(APIView):
    """
    Task 5 — Create Financial Summary Report API
    Combines everything into one response:
    - Financial Summary
    - Expense Summary
    - Income Summary
    - Budget Summary
    - Savings Summary
    - Latest Notifications
    Protected by JWT Authentication.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_date, end_date = parse_date_range(request)

        # 1. Financial Summary
        incomes = Income.objects.filter(user=request.user, income_date__gte=start_date, income_date__lte=end_date)
        expenses = Expense.objects.filter(user=request.user, date_spent__gte=start_date, date_spent__lte=end_date)

        total_income = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        current_balance = total_income - total_expense

        savings = SavingsGoal.objects.filter(user=request.user)
        total_savings = savings.aggregate(total=Sum('saved_amount'))['total'] or Decimal('0.00')

        budgets = Budget.objects.filter(user=request.user, month=start_date.month, year=start_date.year)
        total_budget = budgets.aggregate(total=Sum('budget_amount'))['total'] or Decimal('0.00')
        remaining_budget = total_budget - total_expense

        fin_summary = {
            "total_income": f"{total_income:.2f}",
            "total_expense": f"{total_expense:.2f}",
            "current_balance": f"{current_balance:.2f}",
            "total_savings": f"{total_savings:.2f}",
            "remaining_budget": f"{remaining_budget:.2f}",
            "Total Income": f"{total_income:.2f}",
            "Total Expense": f"{total_expense:.2f}",
            "Current Balance": f"{current_balance:.2f}",
            "Total Savings": f"{total_savings:.2f}",
            "Remaining Budget": f"{remaining_budget:.2f}",
        }

        # 2. Expense Summary
        exp_serializer = ExpenseReportItemSerializer(expenses[:10], many=True)
        exp_summary = {
            "total_expense": f"{total_expense:.2f}",
            "count": expenses.count(),
            "recent_expenses": exp_serializer.data,
            "Total Expense": f"{total_expense:.2f}",
        }

        # 3. Income Summary
        inc_summary = {
            "total_income": f"{total_income:.2f}",
            "count": incomes.count(),
            "Total Income": f"{total_income:.2f}",
        }

        # 4. Budget Summary
        b_summary = {
            "total_budget": f"{total_budget:.2f}",
            "total_spent": f"{total_expense:.2f}",
            "remaining_budget": f"{remaining_budget:.2f}",
            "Total Budget": f"{total_budget:.2f}",
            "Remaining Budget": f"{remaining_budget:.2f}",
        }

        # 5. Savings Summary
        sav_serializer = SavingsReportItemSerializer(savings, many=True)
        sav_summary = {
            "total_savings": f"{total_savings:.2f}",
            "count": savings.count(),
            "goals": sav_serializer.data,
            "Total Savings": f"{total_savings:.2f}",
        }

        # 6. Latest Notifications
        notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        latest_notifs = [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type,
                "priority": n.priority,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            }
            for n in notifs
        ]

        data = {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "financial_summary": fin_summary,
            "expense_summary": exp_summary,
            "income_summary": inc_summary,
            "budget_summary": b_summary,
            "savings_summary": sav_summary,
            "latest_notifications": latest_notifs,

            "Financial Summary": fin_summary,
            "Expense Summary": exp_summary,
            "Income Summary": inc_summary,
            "Budget Summary": b_summary,
            "Savings Summary": sav_summary,
            "Latest Notifications": latest_notifs,
        }
        return Response(data, status=status.HTTP_200_OK)


def generate_pdf_report(report_type, headers, rows, start_date, end_date, user):
    import sys, site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#16233d'),
        spaceAfter=4
    )
    
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#3a4a68'),
        spaceAfter=14
    )
    
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#16233d')
    )
    
    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#16233d')
    )

    title_map = {
        'expenses': 'Expense Report Details',
        'income': 'Income Report Details',
        'savings': 'Savings Goals Report',
        'financial_summary': 'Financial Summary Report'
    }
    report_title = title_map.get(report_type, 'Financial Report')

    elements = []
    elements.append(Paragraph(f"BudgetBuddy — {report_title}", title_style))
    user_identifier = getattr(user, 'username', '') or getattr(user, 'email', '') or 'User'
    elements.append(Paragraph(f"Date Period: {start_date} to {end_date} | Account: {user_identifier}", sub_style))
    elements.append(Spacer(1, 10))

    table_data = []
    hdr_row = [Paragraph(str(h), th_style) for h in headers]
    table_data.append(hdr_row)

    for r in rows:
        row_data = [Paragraph(str(cell), td_style) for cell in r]
        table_data.append(row_data)

    num_cols = max(len(headers), 1)
    col_width = 540.0 / num_cols
    col_widths = [col_width] * num_cols

    t = Table(table_data, colWidths=col_widths)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5f2ec')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dde3df')),
    ]

    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fbf9')))

    t.setStyle(TableStyle(t_style))
    elements.append(t)

    footer_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#788b9c'),
        spaceBefore=16
    )
    elements.append(Paragraph(f"Generated on {datetime.date.today().isoformat()} via BudgetBuddy Financial Platform.", footer_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'
    return response


class ExportReportView(APIView):
    """
    Task 7 — Prepare Export-Ready Data
    Exports data ready for download as CSV, PDF, or JSON.
    Query params:
    - report_type: 'expenses', 'income', 'savings', 'financial_summary'
    - format: 'csv', 'pdf', or 'json'
    - Date parameters: period, start_date, end_date, month, year
    Protected by JWT Authentication.
    """
    permission_classes = [permissions.IsAuthenticated]
    format_kwarg = None

    def perform_content_negotiation(self, request, force=False):
        renderers = self.get_renderers()
        return (renderers[0], renderers[0].media_type)

    def get(self, request):
        report_type = request.query_params.get('report_type', 'expenses')
        export_format = request.query_params.get('format', 'json').lower()
        start_date, end_date = parse_date_range(request)

        headers = []
        rows = []

        if report_type == 'expenses':
            headers = ["Expense Title", "Category", "Amount", "Date", "Description"]
            expenses = Expense.objects.filter(user=request.user, date_spent__gte=start_date, date_spent__lte=end_date).order_by('-date_spent')
            for e in expenses:
                cat = e.category.name if e.category else 'General'
                desc = e.notes or ''
                rows.append([e.title, cat, f"₹{e.amount:.2f}", str(e.date_spent), desc])

        elif report_type == 'income':
            headers = ["Income Title", "Source", "Amount", "Date"]
            incomes = Income.objects.filter(user=request.user, income_date__gte=start_date, income_date__lte=end_date).order_by('-income_date')
            for i in incomes:
                rows.append([i.title, i.source, f"₹{i.amount:.2f}", str(i.income_date)])

        elif report_type == 'savings':
            headers = ["Goal Name", "Target Amount", "Saved Amount", "Remaining Amount", "Progress Percentage"]
            goals = SavingsGoal.objects.filter(user=request.user)
            for g in goals:
                rem = max(Decimal('0.00'), g.target_amount - g.saved_amount)
                pct = float((g.saved_amount / g.target_amount) * Decimal('100.0')) if g.target_amount > 0 else 0.0
                rows.append([g.name, f"₹{g.target_amount:.2f}", f"₹{g.saved_amount:.2f}", f"₹{rem:.2f}", f"{pct:.1f}%"])

        else: # financial_summary
            headers = ["Metric", "Value"]
            total_inc = Income.objects.filter(user=request.user, income_date__gte=start_date, income_date__lte=end_date).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            total_exp = Expense.objects.filter(user=request.user, date_spent__gte=start_date, date_spent__lte=end_date).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            bal = total_inc - total_exp
            sav = SavingsGoal.objects.filter(user=request.user).aggregate(total=Sum('saved_amount'))['total'] or Decimal('0.00')
            rows = [
                ["Total Income", f"₹{total_inc:.2f}"],
                ["Total Expense", f"₹{total_exp:.2f}"],
                ["Current Balance", f"₹{bal:.2f}"],
                ["Total Savings", f"₹{sav:.2f}"]
            ]

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
            return response

        if export_format == 'pdf':
            return generate_pdf_report(report_type, headers, rows, start_date, end_date, request.user)

        return Response({
            "report_type": report_type,
            "exported_at": datetime.datetime.now().isoformat(),
            "start_date": str(start_date),
            "end_date": str(end_date),
            "headers": headers,
            "rows": rows,
            "csv_download_url": f"/api/reports/export/?report_type={report_type}&format=csv",
            "pdf_download_url": f"/api/reports/export/?report_type={report_type}&format=pdf"
        }, status=status.HTTP_200_OK)
