import json
from datetime import datetime, timedelta, date
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.models import User
from django.db.models import Case, When, Q
from .forms import LoginForm, SignUpForm, QuizForm
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .auth_backend import auth
from django.contrib import messages
from .models import QuizResponse, MealPlan, MealPlanDay, Meal, MealFoodItem, Food, FoodJournal
from .genetic_meal_planner import GeneticMealPlanner

def home(request):
    # Check if user has a meal plan
    latest_meal_plan = None
    if request.user.is_authenticated:
        latest_meal_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    context = {
        'latest_meal_plan': latest_meal_plan,
    }
    
    return render(request, "home.html", context)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)   
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth(email=email, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'error': 'Date incorecte'})
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login') 


def quiz_view(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in to access this page.")

    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz_response = form.save(commit=False)
            
            # Ensure request.user is the correct User model
            try:
                user = request.user
                print(f"User ID: {user.id}")
                quiz_response.user = user

                quiz_response.calculate_bmr()
                quiz_response.calculate_tdee()
                quiz_response.calculate_target_calories()

                quiz_response.save()
                messages.success(request, 'Answers saved successfully!')
                return redirect('results_view')
            except User.DoesNotExist:
                return HttpResponseForbidden("User account not found in database.")
    else:
        form = QuizForm()
    
    return render(request, 'quiz.html', {'form': form})


@login_required
def results_view(request):
    try:
        quiz_response = QuizResponse.objects.filter(user=request.user).latest('submitted_at')
        
        target_calories = quiz_response.calculate_target_calories()
        
        macros = calculate_macros(quiz_response)
        
        # verifing if the user has an existing meal plan
        existing_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
        
        context = {
            'quiz_response': quiz_response,
            'macros': macros,
            'target_calories': target_calories,
            'existing_plan': existing_plan
        }
        return render(request, 'results.html', context)
    except QuizResponse.DoesNotExist:
        messages.warning(request, 'You have not completed the quiz yet.')
        return redirect('quiz_view')
    

def calculate_macros(quiz_response):
    """Distribution of macronutrients based on the user's objective"""
    target_calories = quiz_response.calculate_target_calories()
    
    if quiz_response.objective == 1:  # Slăbit
        protein_pct = 0.40  # 40% din calorii
        fat_pct = 0.20      # 30% din calorii
        carbs_pct = 0.40    # 30% din calorii
    
    elif quiz_response.objective == 3:  # Creștere masă musculară
        # Pentru masă musculară: Proteine crescute, carbohidrați crescuți, grăsimi moderate
        protein_pct = 0.30  # 30% din calorii
        fat_pct = 0.25      # 25% din calorii
        carbs_pct = 0.45    # 45% din calorii
    
    elif quiz_response.objective == 2:  # Punere în greutate
        # Pentru punere în greutate: Proteine moderate, carbohidrați crescuți, grăsimi moderate
        protein_pct = 0.25  # 25% din calorii
        fat_pct = 0.30      # 30% din calorii
        carbs_pct = 0.45    # 45% din calorii
        
    else:  # Recompoziție corporală
        # Recompoziție: Balans între proteine, carbohidrați și grăsimi
        protein_pct = 0.30  # 30% din calorii
        fat_pct = 0.30      # 30% din calorii
        carbs_pct = 0.40    # 40% din calorii

    protein_calories = target_calories * protein_pct
    fat_calories = target_calories * fat_pct
    carb_calories = target_calories * carbs_pct
    
    # conversion to grams (1g protein = 4 cal, 1g fat = 9 cal, 1g carb = 4 cal)
    protein_grams = round(protein_calories / 4)
    fat_grams = round(fat_calories / 9)
    carb_grams = round(carb_calories / 4)
    
    return {
        'protein': protein_grams,
        'fat': fat_grams,
        'carbs': carb_grams
    }


@login_required
def view_meal_plan(request, plan_id):
    """Afișează un plan de masă specific"""
    try:
        meal_plan = MealPlan.objects.get(id=plan_id, user=request.user)
    except MealPlan.DoesNotExist:
        messages.error(request, "Meal plan not found or you do not have permission to view it.")
        return redirect('results_view')
    
    meal_plan_days = MealPlanDay.objects.filter(meal_plan=meal_plan).order_by('day')
    
    days_data = []
    for day in meal_plan_days:
        meals = Meal.objects.filter(meal_plan_day=day).order_by(
            Case(
                When(meal_type='breakfast', then=0),
                When(meal_type='lunch', then=1),
                When(meal_type='dinner', then=2),
                default=3
            )
        )
        
        meals_data = []
        for meal in meals:
            food_items = MealFoodItem.objects.filter(meal=meal)
            
            meals_data.append({
                'type': meal.get_meal_type_display(),
                'food_items': food_items,
                'totals': {
                    'calories': meal.total_calories,
                    'protein': meal.total_protein,
                    'carbs': meal.total_carbs,
                    'fat': meal.total_fat
                }
            })
        
        days_data.append({
            'day': day.get_day_display(),
            'meals': meals_data
        })
    
    context = {
        'meal_plan': meal_plan,
        'days': days_data
    }
    
    return render(request, 'view_meal_plan.html', context)


@login_required
def create_view_meal_plan(request):
    """generates a new meal plan based on the user's quiz response"""
    try:
        new_plan = request.GET.get('new_plan') == 'true'

        quiz_response = QuizResponse.objects.filter(user=request.user).latest('submitted_at')
        
        # verfying if the user has an existing meal plan
        existing_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
        
        if existing_plan and not new_plan:
            # redurect to existing plan if it exists
            return redirect('view_meal_plan', plan_id=existing_plan.id)
        
        print(f"generating a new plan for user {request.user}")
        target_calories = quiz_response.calculate_target_calories()
        print(f"Target calories: {target_calories}")
        
        macros = calculate_macros(quiz_response)
        target_protein = macros['protein']
        target_carbs = macros['carbs'] 
        target_fat = macros['fat']
        
        print(f"Food count in database: {Food.objects.count()}")
        
        # using GeneticMealPlanner to create a meal plan
        planner = GeneticMealPlanner(
            user=request.user,
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat
        )
        
        meal_plan = planner.create_meal_plan()
        print(f"Plan generat cu ID: {meal_plan.id}")
        
        return redirect('view_meal_plan', plan_id=meal_plan.id)
        
    except QuizResponse.DoesNotExist:
        messages.warning(request, 'You need to complete the quiz first to generate a meal plan.')
        return redirect('quiz_view')
    except Exception as e:
        print(f"Error at generating meal plan {str(e)}")
        messages.error(request, f'There was an error when generating meal plan {str(e)}')
        return redirect('results_view')
    
@login_required
def debug_meal_plan(request, plan_id):
    plan = MealPlan.objects.get(id=plan_id)
    days = plan.days.all()
    
    output = []
    output.append(f"Plan: {plan.name}, ID: {plan.id}")
    
    for day in days:
        output.append(f"\nDay: {day.get_day_display()}")
        for meal in day.meals.all():
            output.append(f"  Meal: {meal.meal_type}")
            for item in meal.food_items.all():
                output.append(f"    - {item.amount}g {item.food.name} ({item.calories:.0f} kcal)")
    
    return HttpResponse("<pre>" + "\n".join(output) + "</pre>")


@login_required
def search_foods(request):
    """API for searching foods"""
    query = request.GET.get('query', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Caută alimente care conțin query-ul în nume sau categorie
    foods = Food.objects.filter(
        Q(name__icontains=query) | Q(food_category__icontains=query)
    ).order_by('name')[:20]  # limit at 20 results
    
    results = [{
        'id': food.id,
        'name': food.name,
        'calories_per_100g': food.calories_per_100g,
        'protein_per_100g': food.protein_per_100g,
        'carbs_per_100g': food.carbs_per_100g,
        'fat_per_100g': food.fat_per_100g,
        'category': food.food_category or 'Uncategorized'
    } for food in foods]
    
    return JsonResponse({'results': results})

@login_required
def food_journal(request):
    """View for journal of consumed foods"""
    # Obține data din query params sau folosește data curentă
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Obține toate intrările din jurnal pentru data selectată și utilizatorul curent
    journal_entries = FoodJournal.objects.filter(
        user=request.user,
        date=selected_date
    ).order_by('time_consumed')
    
    total_calories = sum(entry.calories for entry in journal_entries)
    total_protein = sum(entry.protein for entry in journal_entries)
    total_carbs = sum(entry.carbs for entry in journal_entries)
    total_fat = sum(entry.fat for entry in journal_entries)
    
    target_calories = None
    target_protein = None
    target_carbs = None
    target_fat = None
    
    try:
        quiz_response = QuizResponse.objects.filter(user=request.user).latest('submitted_at')
        target_calories = quiz_response.calculate_target_calories()
        
        macros = calculate_macros(quiz_response)
        target_protein = macros['protein']
        target_carbs = macros['carbs']
        target_fat = macros['fat']
    except QuizResponse.DoesNotExist:
        pass
    
    # Grupează alimentele consumate pe tipuri de mese
    foods_by_meal = {}
    for meal_type, meal_name in Meal.MEAL_TYPES:
        meal_entries = journal_entries.filter(meal_type=meal_type)
        foods_by_meal[meal_type] = {
            'name': meal_name,
            'items': meal_entries,
            'total_calories': sum(item.calories for item in meal_entries)
        }
    
    # Creează un "obiect jurnal" pentru a fi compatibil cu template-ul
    journal = {
        'target_calories': target_calories,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fat': total_fat,
        'target_protein': target_protein,  # Adăugat obiectivul personalizat de proteine
        'target_carbs': target_carbs,      # Adăugat obiectivul personalizat de carbohidrați
        'target_fat': target_fat,          # Adăugat obiectivul personalizat de grăsimi
        'remaining_calories': target_calories - total_calories if target_calories else None
    }
    
    # Adaugă și procentele atinse pentru macronutrienți
    if target_protein:
        journal['protein_pct'] = min(100, round((total_protein / target_protein) * 100))
    else:
        journal['protein_pct'] = 0
        
    if target_carbs:
        journal['carbs_pct'] = min(100, round((total_carbs / target_carbs) * 100))
    else:
        journal['carbs_pct'] = 0
        
    if target_fat:
        journal['fat_pct'] = min(100, round((total_fat / target_fat) * 100))
    else:
        journal['fat_pct'] = 0
    
    context = {
        'selected_date': selected_date,
        'foods_by_meal': foods_by_meal,
        'meal_types': Meal.MEAL_TYPES,
        'journal': journal,
        'objective': quiz_response.get_objective_display() if quiz_response else None  # Adăugat obiectivul în context
    }
    
    return render(request, 'journal.html', context)

@login_required
def add_food_to_journal(request):
    """API pentru adăugarea unui aliment în jurnal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        food_id = data.get('food_id')
        amount = float(data.get('amount', 100))
        meal_type = data.get('meal_type', 'snack')
        date_str = data.get('date', datetime.today().strftime('%Y-%m-%d'))
        
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # get the food item
        food = Food.objects.get(id=food_id)
        
        # create a new journal entry
        journal_entry = FoodJournal.objects.create(
            user=request.user,
            food=food,
            date=selected_date,
            amount=amount,
            meal_type=meal_type
        )
        
        # return information about the entry
        return JsonResponse({
            'success': True,
            'item': {
                'id': journal_entry.id,
                'name': food.name,
                'amount': amount,
                'calories': journal_entry.calories,
                'protein': journal_entry.protein,
                'carbs': journal_entry.carbs,
                'fat': journal_entry.fat,
                'meal_type': meal_type
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def delete_food_from_journal(request, entry_id):
    """API for deleting a food journal entry"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        entry = FoodJournal.objects.get(id=entry_id, user=request.user)
        entry.delete()
        return JsonResponse({'success': True})
    except FoodJournal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)