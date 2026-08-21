from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from finance.models import Expense, Category
from finance.serializers import ExpenseSerializer
from .services import (
    generate_ai_chat_response,
    generate_ai_insights,
    parse_natural_language_expense,
    run_what_if_simulation,
    get_user_financial_context
)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def chat_api(request):
    """
    POST /api/ai/chat/
    Conversational AI financial assistant endpoint.
    Payload: { "prompt": "Where did I spend most money?" }
    """
    prompt = request.data.get('prompt', '').strip()
    if not prompt:
        return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)

    history = request.data.get('history', [])
    res = generate_ai_chat_response(request.user, prompt, history)
    return Response(res)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def insights_api(request):
    """
    GET /api/ai/insights/
    Returns AI Health Score, Risk Indicators, and Smart Recommendations.
    """
    data = generate_ai_insights(request.user)
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def parse_expense_api(request):
    """
    POST /api/ai/parse-expense/
    Parses natural language text into structured expense data.
    Optionally saves expense to database if auto_save=True.
    Payload: { "text": "Spent $45 on groceries at Walmart", "auto_save": false }
    """
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'Expense text is required.'}, status=status.HTTP_400_BAD_REQUEST)

    auto_save = request.data.get('auto_save', False)
    user = request.user if (request.user and request.user.is_authenticated) else None
    parsed = parse_natural_language_expense(user, text)

    if auto_save:
        if not user:
            return Response({'error': 'You must be logged in to save expenses.'}, status=status.HTTP_401_UNAUTHORIZED)
        if parsed['amount'] > 0:
            cat = None
            if parsed['category_id']:
                cat = Category.objects.filter(id=parsed['category_id']).first()
            if not cat:
                cat = Category.objects.first()

            expense = Expense.objects.create(
                user=user,
                title=parsed['title'],
                amount=parsed['amount'],
                category=cat,
                date_spent=parsed['date_spent'],
                notes=f"Auto-parsed by BudgetBuddy AI from: \"{text}\""
            )
            parsed['created_expense'] = ExpenseSerializer(expense).data

    return Response(parsed)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def simulate_api(request):
    """
    POST /api/ai/simulate/
    Runs what-if scenario simulations for budget and goal planning.
    Payload: { "income_change": 200, "expense_cut_pct": 10, "custom_monthly_savings": 50 }
    """
    user = request.user if (request.user and request.user.is_authenticated) else None
    simulation_results = run_what_if_simulation(user, request.data)
    return Response(simulation_results)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def context_api(request):
    """
    GET /api/ai/context/
    Returns current raw financial context fed into AI.
    """
    ctx = get_user_financial_context(request.user)
    return Response(ctx)
