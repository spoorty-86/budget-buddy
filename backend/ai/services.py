import os
import re
import json
import datetime
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from finance.models import Income, Expense, Budget, SavingsGoal, Category

def get_user_financial_context(user, month=None, year=None):
    """
    Collects complete financial profile of the user for AI context.
    """
    now = timezone.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    inc_qs = Income.objects.filter(user=user, income_date__year=year, income_date__month=month)
    exp_qs = Expense.objects.filter(user=user, date_spent__year=year, date_spent__month=month)
    bud_qs = Budget.objects.filter(user=user, year=year, month=month)
    goals = SavingsGoal.objects.filter(user=user)

    total_income = inc_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expense = exp_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_savings = total_income - total_expense
    savings_rate = float(round((net_savings / total_income * 100), 1)) if total_income > 0 else 0.0

    # Category Breakdown
    cat_breakdown = {}
    cat_qs = exp_qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    for c in cat_qs:
        cat_name = c['category__name'] or 'Uncategorized'
        cat_breakdown[cat_name] = float(c['total'] or 0)

    # Budget tracking
    budgets_detail = []
    total_budget_limit = Decimal('0.00')
    over_budget_count = 0
    for b in bud_qs:
        limit = b.budget_amount or b.monthly_limit or Decimal('0.00')
        total_budget_limit += limit
        spent = Expense.objects.filter(
            user=user, category=b.category, date_spent__year=year, date_spent__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pct = float(round((spent / limit * 100), 1)) if limit > 0 else 0.0
        if spent > limit:
            over_budget_count += 1
        budgets_detail.append({
            'category': b.category.name if b.category else 'General',
            'limit': float(limit),
            'spent': float(spent),
            'remaining': float(max(limit - spent, Decimal('0.00'))),
            'pct_used': pct,
            'is_over': spent > limit
        })

    # Goals
    goals_detail = []
    total_goals_target = Decimal('0.00')
    total_goals_saved = Decimal('0.00')
    for g in goals:
        total_goals_target += g.target_amount
        total_goals_saved += g.saved_amount
        goals_detail.append({
            'id': g.id,
            'name': g.name,
            'target_amount': float(g.target_amount),
            'saved_amount': float(g.saved_amount),
            'progress_pct': float(round((g.saved_amount / g.target_amount * 100), 1)) if g.target_amount > 0 else 0.0,
            'target_date': g.target_date.isoformat() if g.target_date else None
        })

    # Recent Expenses (last 5)
    recent_expenses = []
    for exp in exp_qs.order_by('-date_spent', '-created_at')[:5]:
        recent_expenses.append({
            'title': exp.title,
            'amount': float(exp.amount),
            'category': exp.category.name if exp.category else 'Uncategorized',
            'date': exp.date_spent.isoformat() if hasattr(exp.date_spent, 'isoformat') else str(exp.date_spent)
        })

    # User Profile Info
    user_name = user.get_full_name() or user.username

    return {
        'user_name': user_name,
        'month': month,
        'year': year,
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'net_savings': float(net_savings),
        'savings_rate': savings_rate,
        'category_breakdown': cat_breakdown,
        'total_budget_limit': float(total_budget_limit),
        'over_budget_count': over_budget_count,
        'budgets': budgets_detail,
        'goals': goals_detail,
        'total_goals_target': float(total_goals_target),
        'total_goals_saved': float(total_goals_saved),
        'recent_expenses': recent_expenses
    }


def call_gemini_api(prompt_text, system_instruction=None):
    """
    Calls Google Gemini REST API using urllib standard library to avoid external dependency issues.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None

    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    contents = []
    if system_instruction:
        contents.append({
            "role": "user",
            "parts": [{"text": f"SYSTEM INSTRUCTION:\n{system_instruction}\n\nUSER PROMPT:\n{prompt_text}"}]
        })
    else:
        contents.append({
            "role": "user",
            "parts": [{"text": prompt_text}]
        })

    payload = json.dumps({"contents": contents}).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            candidates = res_json.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', '')
    except Exception as e:
        print(f"[AI Service] Gemini API call error: {e}")
        return None

    return None


def generate_ai_chat_response(user, prompt, history=None):
    """
    Processes chat prompts with financial context and returns intelligent advice.
    """
    context = get_user_financial_context(user)
    
    # 1. Attempt Gemini LLM Call
    system_prompt = (
        "You are BudgetBuddy AI, a friendly, expert personal financial advisor embedded inside the BudgetBuddy app. "
        "You provide actionable, concise, precise financial insights based strictly on the user's real financial data provided below. "
        "Always format currency values using the Indian Rupee symbol (₹).\n\n"
        f"USER FINANCIAL DATA (Current Month: {context['month']}/{context['year']}):\n"
        f"- Name: {context['user_name']}\n"
        f"- Monthly Income: ₹{context['total_income']:.2f}\n"
        f"- Monthly Expenses: ₹{context['total_expense']:.2f}\n"
        f"- Net Savings: ₹{context['net_savings']:.2f} (Savings Rate: {context['savings_rate']}%)\n"
        f"- Spending Categories: {json.dumps(context['category_breakdown'])}\n"
        f"- Budgets: {json.dumps(context['budgets'])}\n"
        f"- Savings Goals: {json.dumps(context['goals'])}\n\n"
        "Guidelines:\n"
        "1. Give direct, concise, quantitative answers answering strictly the user's specific question using Indian Rupees (₹).\n"
        "2. For conversational greetings (e.g. 'how are you', 'hi', 'who are you'), reply politely and conversationally without dumping raw financial tables unless specifically asked.\n"
        "3. Keep responses clear and well-structured."
    )

    llm_response = call_gemini_api(prompt, system_instruction=system_prompt)
    if llm_response:
        return {
            'reply': llm_response,
            'source': 'Gemini AI',
            'context_summary': {
                'income': context['total_income'],
                'expense': context['total_expense'],
                'savings_rate': context['savings_rate']
            }
        }

    # 2. Rule-Based Intelligent Fallback AI Engine
    p_lower = prompt.lower().strip()

    # Conversational Intent A: "how are you", "how are u", "how do you do"
    if any(k in p_lower for k in ['how are you', 'how are u', 'how do you do', 'how is it going', 'how are things', 'how r u']):
        reply = f"I'm doing great, thank you for asking! 😊 I'm here and ready to help you analyze your spending, check budget limits, or track your savings goals. How can I assist you today, {context['user_name']}?"
        return {'reply': reply, 'source': 'BudgetBuddy AI', 'context_summary': {}}

    # Conversational Intent B: Greetings ("hi", "hello", "hey", "good morning")
    elif p_lower in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings'] or any(p_lower.startswith(k) for k in ['hi ', 'hello ', 'hey ']):
        reply = f"Hello {context['user_name']}! 👋 How can I assist you with your finances today?"
        return {'reply': reply, 'source': 'BudgetBuddy AI', 'context_summary': {}}

    # Conversational Intent C: Identity ("who are you", "what are you", "what can you do")
    elif any(k in p_lower for k in ['who are you', 'what are you', 'what can you do', 'your name', 'about you']):
        reply = f"I am your BudgetBuddy AI Financial Companion! 🤖\n\nI can help you:\n• Track your income, expenses, and net savings\n• Audit category spending and budget limits\n• Answer affordability questions\n• Parse natural language expenses and simulate savings goals."
        return {'reply': reply, 'source': 'BudgetBuddy AI', 'context_summary': {}}

    # Conversational Intent D: Gratitude ("thank you", "thanks", "awesome")
    elif any(k in p_lower for k in ['thank you', 'thanks', 'thx', 'awesome', 'great job', 'perfect', 'thank u']):
        reply = f"You're very welcome, {context['user_name']}! 😊 Let me know if you need any more financial insights!"
        return {'reply': reply, 'source': 'BudgetBuddy AI', 'context_summary': {}}

    # Financial Intent 1: Direct Saved / Net Savings Question
    elif any(k in p_lower for k in ['how much i saved', 'how much saved', 'amount i saved', 'amount saved', 'total saved', 'my savings', 'saved amount', 'net savings', 'how much did i save', 'saved this month', 'how much save']):
        reply = f"💰 You have saved **₹{context['net_savings']:.2f}** this month (Savings Rate: **{context['savings_rate']}%**)."
        if context['total_goals_saved'] > 0:
            reply += f"\n🏦 Total saved across Savings Goals: **₹{context['total_goals_saved']:.2f}**."
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'net_savings': context['net_savings']}}

    # Financial Intent 2: Direct Income Question
    elif any(k in p_lower for k in ['income', 'salary', 'how much i earned', 'total earnings', 'earned this month', 'how much income']):
        reply = f"💵 Your total income for this month is **₹{context['total_income']:.2f}**."
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'total_income': context['total_income']}}

    # Financial Intent 3: Direct Expense / Spending Question
    elif any(k in p_lower for k in ['total expense', 'total spent', 'how much spent', 'how much i spent', 'total spending', 'total expenditure']):
        reply = f"💸 Your total spending for this month is **₹{context['total_expense']:.2f}**."
        if context['category_breakdown']:
            top_cat = max(context['category_breakdown'], key=context['category_breakdown'].get)
            reply += f"\n📊 Highest spending category: **{top_cat}** (₹{context['category_breakdown'][top_cat]:.2f})."
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'total_expense': context['total_expense']}}

    # Financial Intent 4: High Expense / Spending Check
    elif any(k in p_lower for k in ['highest', 'top spending', 'where does my money go', 'spend most', 'categories', 'category']):
        if not context['category_breakdown']:
            reply = f"Hi {context['user_name']}! You haven't recorded any expenses for this month yet. Add your expenses to see detailed category analysis!"
        else:
            top_cat = max(context['category_breakdown'], key=context['category_breakdown'].get)
            top_amt = context['category_breakdown'][top_cat]
            pct = round((top_amt / context['total_expense'] * 100), 1) if context['total_expense'] > 0 else 0
            reply = (
                f"📊 **Spending Analysis for {context['user_name']}**:\n\n"
                f"Your highest spending category this month is **{top_cat}** at **₹{top_amt:.2f}**, which represents **{pct}%** of your total monthly expenditure (₹{context['total_expense']:.2f}).\n\n"
                f"💡 **Recommendation**: Setting a strict limit in the **Budgets** section for `{top_cat}` could save you roughly **₹{(top_amt * 0.15):.2f}** per month!"
            )
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'top_category': top_cat if context['category_breakdown'] else None}}

    # Financial Intent 5: Budget Status & Over-spending
    elif any(k in p_lower for k in ['budget', 'overbudget', 'limit', 'spending limit', 'am i spending too much']):
        if not context['budgets']:
            reply = (
                f"Hi {context['user_name']}! You don't have any budget limits set up for this month.\n\n"
                f"💡 **Tip**: Head over to the **Budgets** page to set target spending limits for categories like Dining, Groceries, or Shopping!"
            )
        else:
            over = [b for b in context['budgets'] if b['is_over']]
            if over:
                over_names = ", ".join([f"**{b['category']}** (₹{b['spent']:.2f} / ₹{b['limit']:.2f})" for b in over])
                reply = (
                    f"⚠️ **Budget Alert for {context['user_name']}**:\n\n"
                    f"You have exceeded your budget in **{len(over)} category/categories**:\n"
                    f"• {over_names}\n\n"
                    f"Total monthly budget limit: **₹{context['total_budget_limit']:.2f}** | Total Spent: **₹{context['total_expense']:.2f}**."
                )
            else:
                reply = (
                    f"✅ **Great job, {context['user_name']}!** All your budgets are currently within limits.\n\n"
                    f"Total Budgeted Limit: **₹{context['total_budget_limit']:.2f}** | Total Spent: **₹{context['total_expense']:.2f}**.\n"
                    f"You have **₹{(context['total_budget_limit'] - context['total_expense']):.2f}** remaining across your budgeted categories."
                )
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'over_budget_count': context['over_budget_count']}}

    # Financial Intent 6: Savings Goals & Progress
    elif any(k in p_lower for k in ['savings', 'goal', 'vacation', 'emergency fund', 'save more', 'target']):
        if not context['goals']:
            reply = (
                f"Hi {context['user_name']}! You currently have no active savings goals.\n\n"
                f"🎯 **AI Suggestion**: Creating savings goals (e.g. Emergency Fund, Vacation, New Car) helps keep you motivated. Try creating one in **Savings Goals**!"
            )
        else:
            goal_summaries = []
            for g in context['goals']:
                goal_summaries.append(f"• **{g['name']}**: ₹{g['saved_amount']:.2f} of ₹{g['target_amount']:.2f} ({g['progress_pct']}%)")
            goals_text = "\n".join(goal_summaries)
            
            rate_advice = ""
            if context['savings_rate'] < 20:
                rate_advice = f"\n\n💡 **Boost Strategy**: Your current savings rate is **{context['savings_rate']}%**. Financial experts recommend striving for a 20% savings rate (₹{(context['total_income'] * 0.2):.2f}/mo)."
            else:
                rate_advice = f"\n\n🌟 **Awesome Work**: Your current savings rate is a healthy **{context['savings_rate']}%**!"

            reply = (
                f"🏦 **Savings Goals Overview**:\n\n"
                f"{goals_text}{rate_advice}\n\n"
                f"Your total saved across all goals is **₹{context['total_goals_saved']:.2f}** out of **₹{context['total_goals_target']:.2f}** target."
            )
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'total_goals_saved': context['total_goals_saved']}}

    # Financial Intent 7: Affordability / Purchase query
    elif any(k in p_lower for k in ['can i afford', 'buy', 'purchase', 'cost', 'should i spend']):
        match = re.search(r'(?:₹|rs\.?|\$)?\s*(\d+(?:\.\d{1,2})?)', prompt, re.IGNORECASE)
        item_cost = float(match.group(1)) if match else 100.0

        if item_cost <= context['net_savings']:
            remaining_after = context['net_savings'] - item_cost
            reply = (
                f"👍 **Purchase Analysis**: Yes, based on your current net savings of **₹{context['net_savings']:.2f}**, you can afford a **₹{item_cost:.2f}** expense.\n\n"
                f"• Net Balance Before: **₹{context['net_savings']:.2f}**\n"
                f"• Net Balance After: **₹{remaining_after:.2f}**"
            )
        else:
            shortfall = item_cost - context['net_savings']
            reply = (
                f"⚠️ **Caution Recommended**: Buying a **₹{item_cost:.2f}** item right now would result in a shortfall of **₹{shortfall:.2f}** based on your current net balance of **₹{context['net_savings']:.2f}**."
            )
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'net_savings': context['net_savings']}}

    # Financial Intent 8: Full Financial Summary Explicit Request
    elif any(k in p_lower for k in ['summary', 'overview', 'details', 'full report', 'all details', 'financial status', 'snapshot']):
        reply = (
            f"📊 **AI Financial Snapshot for {context['user_name']}**:\n\n"
            f"💰 **Monthly Income**: ₹{context['total_income']:.2f}\n"
            f"💸 **Monthly Expenses**: ₹{context['total_expense']:.2f}\n"
            f"📈 **Net Balance**: ₹{context['net_savings']:.2f} (Savings Rate: {context['savings_rate']}%)\n\n"
            f"Feel free to ask me questions like:\n"
            f"• *\"How much amount i saved?\"*\n"
            f"• *\"Where am I spending the most?\"*\n"
            f"• *\"Am I over budget in any category?\"*\n"
            f"• *\"Can I afford a ₹500 purchase?\"*"
        )
        return {'reply': reply, 'source': 'BudgetBuddy Financial Intelligence Engine', 'context_summary': {'income': context['total_income'], 'expense': context['total_expense']}}

    # Default Intent: Helpful Assistant Fallback
    else:
        reply = (
            f"I'm here to help with your finances, {context['user_name']}! 😊\n\n"
            f"You can ask me questions like:\n"
            f"• *\"How much amount i saved?\"*\n"
            f"• *\"Where am I spending the most?\"*\n"
            f"• *\"Am I over budget in any category?\"*\n"
            f"• *\"Can I afford a ₹500 purchase?\"*"
        )
        return {'reply': reply, 'source': 'BudgetBuddy AI', 'context_summary': {}}


def generate_ai_insights(user):
    """
    Generates AI Health Score, Risk Indicators, and Smart Recommendations.
    """
    ctx = get_user_financial_context(user)
    income = ctx['total_income']
    expense = ctx['total_expense']
    net = ctx['net_savings']
    savings_rate = ctx['savings_rate']
    over_budget_count = ctx['over_budget_count']
    
    # Calculate AI Health Score (0 - 100)
    score = 50.0  # baseline score
    
    # Factor 1: Savings rate (up to +35 points)
    if savings_rate >= 30:
        score += 35
    elif savings_rate >= 20:
        score += 28
    elif savings_rate >= 10:
        score += 18
    elif savings_rate > 0:
        score += 8
    else:
        score -= 15  # deficit spending penalty

    # Factor 2: Budget discipline (up to +20 points)
    if ctx['budgets']:
        if over_budget_count == 0:
            score += 20
        else:
            score -= (over_budget_count * 8)
    else:
        score += 5

    # Factor 3: Savings Goals engagement (+15 points)
    if ctx['goals']:
        score += 15
        if ctx['total_goals_saved'] > 0:
            score += 5

    # Clamp score 0 - 100
    score = max(0, min(100, int(round(score))))

    if score >= 85:
        grade = 'A+'
        status = 'Excellent Financial Health'
        status_color = '#10b981'
    elif score >= 70:
        grade = 'A'
        status = 'Strong Financial Health'
        status_color = '#3b82f6'
    elif score >= 55:
        grade = 'B'
        status = 'Moderate / Stable'
        status_color = '#f59e0b'
    elif score >= 40:
        grade = 'C'
        status = 'Needs Attention'
        status_color = '#f97316'
    else:
        grade = 'D'
        status = 'Critical / Over-spending'
        status_color = '#ef4444'

    # Build Insights List
    insights = []
    
    # Insight 1: Savings Rate Analysis
    if savings_rate >= 20:
        insights.append({
            'type': 'success',
            'title': 'High Savings Efficiency',
            'description': f'Your savings rate of {savings_rate}% exceeds the recommended 20% benchmark.',
            'action': 'Consider allocating excess savings into your long-term investment or high-yield savings goals.'
        })
    elif savings_rate > 0:
        insights.append({
            'type': 'warning',
            'title': 'Savings Rate Below Benchmark',
            'description': f'Your savings rate is {savings_rate}%. Benchmark standard is 20%.',
            'action': f'Try trimming ₹{(income * 0.1):.2f} from non-essential spending to reach a 20% savings target.'
        })
    else:
        insights.append({
            'type': 'danger',
            'title': 'Net Deficit Spending Warning',
            'description': f'Expenses (₹{expense:.2f}) currently exceed income (₹{income:.2f}) by ₹{abs(net):.2f}.',
            'action': 'Review your largest expense categories immediately to prevent accumulating debt.'
        })

    # Insight 2: Category Concentration Risk
    if ctx['category_breakdown']:
        top_cat, top_amt = max(ctx['category_breakdown'].items(), key=lambda x: x[1])
        if expense > 0 and (top_amt / expense) > 0.4:
            insights.append({
                'type': 'warning',
                'title': f'High Concentration in {top_cat}',
                'description': f'{top_cat} accounts for {round(top_amt/expense*100, 1)}% of your total spend this month (₹{top_amt:.2f}).',
                'action': f'Set a category budget limit for {top_cat} to balance overall cashflow.'
            })

    # Insight 3: Budget Overruns
    if over_budget_count > 0:
        insights.append({
            'type': 'danger',
            'title': f'{over_budget_count} Category Budget(s) Exceeded',
            'description': 'One or more of your active budget limits have been breached.',
            'action': 'Check your Budgets dashboard and re-adjust discretionary allocations.'
        })

    # Insight 4: Savings Goals Progress
    if ctx['goals']:
        insights.append({
            'type': 'info',
            'title': f'Active Savings Target',
            'description': f'You have saved ₹{ctx["total_goals_saved"]:.2f} toward your ₹{ctx["total_goals_target"]:.2f} goal target.',
            'action': 'Keep up consistent monthly contributions to maintain milestone momentum.'
        })

    # Month-end Forecast
    now = timezone.now()
    days_in_month = 30
    days_passed = max(1, now.day)
    daily_burn_rate = expense / days_passed
    projected_month_end_expense = daily_burn_rate * days_in_month
    projected_net_savings = income - round(projected_month_end_expense, 2)

    return {
        'health_score': score,
        'grade': grade,
        'status': status,
        'status_color': status_color,
        'metrics': {
            'income': ctx['total_income'],
            'expense': ctx['total_expense'],
            'net_savings': ctx['net_savings'],
            'savings_rate': ctx['savings_rate'],
            'total_budget': ctx['total_budget_limit'],
            'over_budget_count': ctx['over_budget_count']
        },
        'insights': insights,
        'forecast': {
            'days_elapsed': days_passed,
            'daily_burn_rate': round(daily_burn_rate, 2),
            'projected_total_expense': round(projected_month_end_expense, 2),
            'projected_net_savings': float(projected_net_savings)
        }
    }


def parse_natural_language_expense(user, text):
    """
    Parses natural language input like "Spent ₹450 on groceries at Target"
    into structured expense fields: title, amount, category, date.
    """
    text_clean = text.strip()
    
    # 1. Regex parse amount (supports ₹, rs., rs, inr, $)
    amount_match = re.search(r'(?:spent|₹|rs\.?|inr|\$|paid|for|cost)?\s*(?:₹|rs\.?|inr|\$)?\s*(\d+(?:\.\d{1,2})?)', text_clean, re.IGNORECASE)
    amount = float(amount_match.group(1)) if amount_match else 0.0

    # 2. Extract Category matching user's DB categories
    categories = Category.objects.all()
    matched_category = None
    text_lower = text_clean.lower()
    
    for cat in categories:
        if cat.name.lower() in text_lower:
            matched_category = cat
            break
            
    if not matched_category:
        # Fallback heuristic mapping
        mapping = {
            'food': ['groceries', 'supermarket', 'walmart', 'lunch', 'dinner', 'food', 'restaurant', 'starbucks', 'coffee', 'burger', 'pizza', 'swiggy', 'zomato'],
            'transport': ['gas', 'fuel', 'uber', 'lyft', 'ola', 'taxi', 'bus', 'train', 'flight', 'parking', 'petrol'],
            'bills': ['electricity', 'water', 'internet', 'wifi', 'rent', 'bill', 'utility', 'subscription', 'netflix'],
            'shopping': ['clothes', 'amazon', 'target', 'flipkart', 'shoes', 'electronics', 'shopping'],
            'entertainment': ['movie', 'tickets', 'game', 'concert', 'party']
        }
        for cat_key, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                matched_category = Category.objects.filter(name__icontains=cat_key).first()
                if matched_category:
                    break

    # 3. Clean Title
    title = text_clean
    # Remove common lead words
    title = re.sub(r'^(spent|paid|bought|cost)\s*', '', title, flags=re.IGNORECASE).strip()
    if title:
        title = title[0].upper() + title[1:]

    # 4. Date parsing (today or yesterday)
    today = datetime.date.today()
    date_spent = today
    if 'yesterday' in text_lower:
        date_spent = today - datetime.timedelta(days=1)

    return {
        'title': title or 'Parsed Expense',
        'amount': amount,
        'category_id': matched_category.id if matched_category else None,
        'category_name': matched_category.name if matched_category else 'General',
        'date_spent': date_spent.isoformat(),
        'original_text': text_clean
    }


def run_what_if_simulation(user, params):
    """
    Simulates financial changes based on user inputs.
    Params:
      - income_change: float (+ or -)
      - expense_cut_pct: float (0 - 100)
      - custom_monthly_savings: float
    """
    ctx = get_user_financial_context(user)
    base_income = ctx['total_income']
    base_expense = ctx['total_expense']
    base_net = ctx['net_savings']

    income_change = float(params.get('income_change', 0))
    expense_cut_pct = float(params.get('expense_cut_pct', 0))
    custom_monthly_savings = float(params.get('custom_monthly_savings', 0))

    new_income = max(0.0, base_income + income_change)
    new_expense = max(0.0, base_expense * (1 - (expense_cut_pct / 100.0)))
    new_net = new_income - new_expense + custom_monthly_savings
    new_savings_rate = float(round((new_net / new_income * 100), 1)) if new_income > 0 else 0.0

    monthly_gain = new_net - base_net
    yearly_projected_gain = monthly_gain * 12

    # Goal Impact
    goals_impact = []
    for g in ctx['goals']:
        remaining = g['target_amount'] - g['saved_amount']
        if remaining > 0:
            current_months_to_goal = (remaining / base_net) if base_net > 0 else 999
            new_months_to_goal = (remaining / new_net) if new_net > 0 else 999
            time_saved_months = max(0.0, round(current_months_to_goal - new_months_to_goal, 1))
            goals_impact.append({
                'name': g['name'],
                'remaining': remaining,
                'current_months_left': round(current_months_to_goal, 1) if current_months_to_goal < 900 else 'N/A',
                'new_months_left': round(new_months_to_goal, 1) if new_months_to_goal < 900 else 'N/A',
                'months_faster': time_saved_months
            })

    return {
        'baseline': {
            'income': base_income,
            'expense': base_expense,
            'net_savings': base_net,
            'savings_rate': ctx['savings_rate']
        },
        'simulated': {
            'income': new_income,
            'expense': new_expense,
            'net_savings': new_net,
            'savings_rate': new_savings_rate
        },
        'diff': {
            'monthly_savings_diff': round(monthly_gain, 2),
            'yearly_projected_diff': round(yearly_projected_gain, 2),
            'savings_rate_diff': round(new_savings_rate - ctx['savings_rate'], 1)
        },
        'goals_impact': goals_impact
    }
