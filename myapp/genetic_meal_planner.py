import random
import numpy as np
from django.db.models import Q
from .models import Food, MealPlan, MealPlanDay, Meal, MealFoodItem
import time

class GeneticMealPlanner:
    """Class for Genetic algorithm-based meal planner for creating personalized meal plans."""
    
    def __init__(self, user, target_calories, target_protein, target_carbs, target_fat):
        self.user = user
        self.target_calories = target_calories
        self.target_protein = target_protein
        self.target_carbs = target_carbs
        self.target_fat = target_fat
        
        # parameters for genetic algorithm
        self.population_size = 130
        self.generations = 35
        self.mutation_rate = 0.2
        self.elite_size = 5
            
        # meal distribution percentages
        self.meal_distribution = {
            'breakfast': 0.25, 
            'lunch': 0.35,    
            'dinner': 0.30, 
            'snack': 0.10 
        }

        self.unhealthy_foods = ['pasta', 'pizza', 'cake', 'cookies', 'sugar', 'candy', 
                          'chocolate', 'soda', 'fries', 'chips', 'ice cream', 'burrito', 'croissant']

        self.meal_categories = {
            'breakfast': ['cereal','toast', 'oats', 'egg', 'milk', 'yogurt', 'bread', 'cheese', 'apple', 
                          'banana', 'fruit','bacon','sausage', 'bagel', 'bread whole-wheat', 'french toast',
                          'greek yogurt','egg whole', 'egg white'],
            'lunch': ['chicken', 'turkey', 'beef', 'fish', 'rice', 'potato', 'vegetable', 'beans', 'lentils', 'soup', 'salad', 'corn'
                            , 'green beans', 'broccoli', 'spinach', 'carrot', 'bread', 'bulgur','chicken breast',
                            'tomato','tofu'],
            'dinner': ['chicken', 'beef', 'asparagus', 'fish', 'salmon','sweet potato', 'rice', 'potato', 'vegetable', 'broccoli', 'spinach', 'asparagus', 'green beans',
                             'cauliflower', 'corn', 'carrot','chicken breast','tomato','tofu'],
            'snack': ['fruit', 'apple', 'banana', 'orange', 'grape', 'strawberry', 'blueberry', 'nuts', 
                      'yogurt', 'peanuts roasted', 'peanuts','almonds roasted','greek yogurt', 'protein bar']
        }
        
        # initialize food cache
        self.food_cache = self._init_food_cache()
    
    def _init_food_cache(self):
        """ Initialize food cache by loading foods from database and categorizing them by meal type.
        
        Excludes unhealthy foods and organizes available foods into categories suitable
        for different meal types (breakfast, lunch, dinner, snack)."""
        food_cache = {}
        
        unhealthy_query = Q()
        for unhealthy_food in self.unhealthy_foods:
            unhealthy_query |= Q(name__icontains=unhealthy_food)


        # load all healthy foods from the database
        all_foods = list(Food.objects.exclude(
            Q(calories_per_100g=0) | unhealthy_query
        ).values('id', 'name', 'calories_per_100g', 
                'protein_per_100g', 'carbs_per_100g', 'fat_per_100g', 'food_category'))
        
        print(f"Total healthy foods: {len(all_foods)}")
        
        # define functional categories for meals
        meal_functional_categories = {
            'breakfast': {
                'main': ['egg', 'cereal', 'oats', 'yogurt', 'greek yogurt', 'bacon', 'sausage','egg whole','egg white'],
                'side': ['banana', 'milk', 'yogurt', 'bread','toast', 'bagel','bread whole-wheat', 'french toast',
                          ], 
                'max_items': 3  
            },
            'lunch': {
                'protein': ['chicken', 'beef', 'fish', 'salmon', 'beans', 'lentils','turkey','chicken breast',
                            'tofu'], 
                'carbs': ['rice', 'potato', 'bread', 'bulgur'],  
                'veggies': ['vegetable', 'broccoli', 'spinach', 'salad', 'carrot', 'beans', 'lentils', 'corn'
                            , 'green beans','tomato'], 
                'max_items': 5
            },
            'dinner': {
                'protein': ['chicken', 'beef', 'fish', 'salmon','chicken breast','tofu'],  
                'carbs': ['rice', 'potato','sweet_potato'],  
                'veggies': ['vegetable', 'broccoli', 'spinach', 'carrot','asparagus', 'green beans',
                             'cauliflower', 'corn','tomato'],  
                'max_items': 5
            },
            'snack': {
                'items': ['fruit', 'apple', 'banana', 'strawberry', 'nuts', 'yogurt', 'blueberries', 
                          'peanuts', 'peanuts roasted', 'almonds roasted', 'greek yogurt','protein bar'],
                'max_items': 2  
            }
        }

        # group foods by category
        foods_by_category = {}
        for food in all_foods:
            category = food.get('food_category', '').lower()
            if category not in foods_by_category:
                foods_by_category[category] = []
            foods_by_category[category].append(food)
        
        # allocate foods to meal types based on defined categories
        for meal_type, categories in self.meal_categories.items():
            food_cache[meal_type] = []
            
            for category in categories:
                if category in foods_by_category:
                    food_cache[meal_type].extend(foods_by_category[category])
            
            print(f"{meal_type}: {len(food_cache[meal_type])} foods attributed {', '.join(categories)}")
            
            # if there are not enough foods for this meal type, add from other categories
            if len(food_cache[meal_type]) < 10:
                print(f"ATTENTION: not enough foods for: {meal_type}, adding other categories")
                for category, foods in foods_by_category.items():
                    if category not in categories:
                        food_cache[meal_type].extend(foods)
        
        # add functional categories to the cache
        food_cache['functional'] = meal_functional_categories
        
        return food_cache
    
    def create_meal_plan(self, name="Plan personalizat (genetic)", description=None):
        """Create a complete 7-day meal plan using genetic algorithms."""
        start_time = time.time()
        
        # create meal plan object
        meal_plan = MealPlan.objects.create(
            user=self.user,
            name=name,
            description=description or f"Genetic plan optimised for {self.target_calories:.0f} calories daily",
            target_calories=self.target_calories,
            target_protein=self.target_protein,
            target_carbs=self.target_carbs,
            target_fat=self.target_fat
        )
        
        # Track best meals for each meal type
        best_meals = {
            'breakfast': {'best_fitness': 0, 'best_meal': None, 'all_scores': []},
            'lunch': {'best_fitness': 0, 'best_meal': None, 'all_scores': []},
            'dinner': {'best_fitness': 0, 'best_meal': None, 'all_scores': []},
            'snack': {'best_fitness': 0, 'best_meal': None, 'all_scores': []}
        }

        # Generate meal plan days
        for day_num in range(1, 8):
            meal_plan_day = MealPlanDay.objects.create(
                meal_plan=meal_plan,
                day=day_num
            )
            
            # Generate meals for the day
            for meal_type, pct in self.meal_distribution.items():
                meal_calories = self.target_calories * pct
                meal_protein = self.target_protein * pct
                meal_carbs = self.target_carbs * pct
                meal_fat = self.target_fat * pct
                
                meal = Meal.objects.create(
                    meal_plan_day=meal_plan_day,
                    meal_type=meal_type
                )
                
                # Generate foods for the meal using genetic algorithm
                fitness_score, food_items = self._generate_meal_foods_genetic(
                    meal, meal_type, meal_calories, meal_protein, meal_carbs, meal_fat
                )
                
                # Track fitness scores for averages
                best_meals[meal_type]['all_scores'].append(fitness_score)
                
                # Update best meal if this one is better
                if fitness_score > best_meals[meal_type]['best_fitness']:
                    best_meals[meal_type]['best_fitness'] = fitness_score
                    best_meals[meal_type]['best_meal'] = {
                        'day': day_num,
                        'foods': food_items,
                        'fitness': fitness_score
                    }
        
        # Calculate and display statistics
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate overall average of all best meals
        all_best_scores = [data['best_fitness'] for data in best_meals.values() if data['best_fitness'] > 0]
        best_meals_average = sum(all_best_scores) / len(all_best_scores) if all_best_scores else 0
        
        # Print comprehensive meal generation statistics
        print("\n" + "="*70)
        print("📊 MEAL GENERATION STATISTICS")
        print("="*70)
        
        print(f"🕐 Total Generation Time: {total_time:.2f} seconds")
        print(f"📊 Time per meal: {total_time/28:.3f} seconds (28 meals total)")
        
        print(f"\n🎯 FITNESS SCORE ANALYSIS:")
        print("-" * 70)
        print(f"{'Meal Type':<12} {'Best Score':<12} {'Avg Score':<12} {'Day':<8} {'Performance'}")
        print("-" * 70)
        
        overall_scores = []
        
        for meal_type, data in best_meals.items():
            all_scores = data['all_scores']
            best_score = data['best_fitness']
            avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
            best_day = data['best_meal']['day'] if data['best_meal'] else 'N/A'
            
            # Add to overall calculation
            overall_scores.extend(all_scores)
            
            # Performance indicator
            if avg_score >= 0.8:
                performance = "🟢 Excellent"
            elif avg_score >= 0.7:
                performance = "🟡 Good"
            elif avg_score >= 0.6:
                performance = "🟠 Fair"
            else:
                performance = "🔴 Needs Work"
            
            print(f"{meal_type.capitalize():<12} {best_score:<12.4f} {avg_score:<12.4f} {best_day:<8} {performance}")
        
        # Overall statistics
        overall_best = max(overall_scores) if overall_scores else 0
        overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        print("-" * 70)
        print(f"{'OVERALL':<12} {overall_best:<12.4f} {overall_avg:<12.4f} {'All':<8} {'Summary'}")
        print(f"{'BEST MEALS AVG':<12} {'-':<12} {best_meals_average:<12.4f} {'All':<8} {'Best Only'}")
        print("-" * 70)
        
        # Print summary of best meals found
        print(f"\n🏆 BEST MEALS BY TYPE:")
        print("-" * 50)
        
        for meal_type, data in best_meals.items():
            if data['best_meal']:
                best = data['best_meal']
                print(f"\n{meal_type.upper()} - Day {best['day']} (Score: {best['fitness']:.4f})")
                
                # Display top 3 foods in best meal
                sorted_foods = sorted(best['foods'], key=lambda x: x[1], reverse=True)[:3]
                for i, (food_id, amount) in enumerate(sorted_foods, 1):
                    try:
                        food = Food.objects.get(id=food_id)
                        print(f"  {i}. {food.name}: {amount:.0f}g")
                    except Food.DoesNotExist:
                        print(f"  {i}. Food ID {food_id}: {amount:.0f}g")
        
        return meal_plan
    
    def _generate_meal_foods_genetic(self, meal, meal_type, target_calories, target_protein, target_carbs, target_fat):
        """Generate food items for a specific meal using genetic algorithm optimization.
        
        Creates a population of meal candidates, evolves them through multiple generations,
        and selects the best combination of foods that meets nutritional targets."""
        foods_for_meal = self.food_cache[meal_type]
        
        if not foods_for_meal:
            print(f"WARNING: No foods for: {meal_type}!")
            return 0.0, []
        
        print(f"Generating genetic meal for {meal_type}: {len(foods_for_meal)} available foods")
        
        # create initial population of meal candidates
        population = self._initialize_population(foods_for_meal, target_calories, meal_type)
        
        # evolve the population to find the best meal
        best_meal = self._evolve_population(
            population, 
            foods_for_meal, 
            target_calories, 
            target_protein, 
            target_carbs, 
            target_fat
        )
        
        print(f"Best meal: {len(best_meal)} foods")
        
        # calculate fitness score for the best meal
        foods_dict = {food['id']: food for food in foods_for_meal}
        fitness_score = self._fitness_score(best_meal, foods_dict, target_calories, target_protein, target_carbs, target_fat)

        # save best meal to database
        try:
            for food_id, amount in best_meal:
                try:
                    food = Food.objects.get(id=food_id)
                    item = MealFoodItem.objects.create(
                        meal=meal,
                        food=food,
                        amount=amount
                    )
                    print(f"  - food added: {food.name} ({amount:.1f}g), ID: {food.id}")
                except Food.DoesNotExist:
                    print(f"ERROR: food with id {food_id} does not exist in database")
                except Exception as e:
                    print(f"ERROR saving food {food_id}: {str(e)}")
        except Exception as e:
            print(f"ERROR saving meal: {str(e)}")
        
        return fitness_score, best_meal
    
    def _initialize_population(self, foods, target_calories, meal_type):
        """Create initial population of meal candidates with structured food combinations."""
        population = []
        
        # meal_type = None
        # for mt in self.meal_distribution.keys():
        #     if self.food_cache[mt] == foods:
        #         meal_type = mt
        #         break
        
        # if not meal_type:
        #     meal_type = random.choice(list(self.meal_distribution.keys()))
        #     print(f"Nu am putut determina tipul de masă, folosim implicit: {meal_type}")
        print(f"initialize population for : {meal_type}")


        # get functional categories for this meal type
        func_categories = self.food_cache['functional'][meal_type]
        
        for _ in range(self.population_size):
            meal = []
            current_calories = 0
            
            if meal_type in ['lunch', 'dinner']:
                # add protein source
                protein_foods = [f for f in foods if any(cat in f.get('food_category', '').lower() for cat in func_categories['protein'])]
                if protein_foods:
                    protein = random.choice(protein_foods)
                    amount = random.uniform(60, 120)
                    meal.append((protein['id'], amount))
                    current_calories += (amount / 100) * protein['calories_per_100g']
                
                # add carbohydrate source
                carb_foods = [f for f in foods if any(cat in f.get('food_category', '').lower() for cat in func_categories['carbs'])]
                if carb_foods:
                    carb = random.choice(carb_foods)
                    
                    amount = random.uniform(70, 150)
                    meal.append((carb['id'], amount))
                    current_calories += (amount / 100) * carb['calories_per_100g']
                
                # add veggetable
                veggie_foods = [f for f in foods if any(cat in f.get('food_category', '').lower() for cat in func_categories['veggies'])]
                if veggie_foods:
                    veggie = random.choice(veggie_foods)
                    
                    amount = random.uniform(100, 200)
                    meal.append((veggie['id'], amount))
                    current_calories += (amount / 100) * veggie['calories_per_100g']
            
            elif meal_type == 'breakfast':
                # add main food
                main_foods = [f for f in foods if any(cat in f.get('food_category', '').lower() for cat in func_categories['main'])]
                if main_foods:
                    main_food = random.choice(main_foods)
                    # quantity for main food (50-100g)
                    amount = random.uniform(50, 100)
                    meal.append((main_food['id'], amount))
                    current_calories += (amount / 100) * main_food['calories_per_100g']
                
                # add side food (e.g., toast, fruit)
                side_foods = [f for f in foods if any(cat in f.get('food_category', '').lower() for cat in func_categories['side'])]
                if side_foods:
                    # exclude food already used as main
                    available_sides = [f for f in side_foods if f['id'] != main_food['id']] if main_foods else side_foods
                    if available_sides:
                        side_food = random.choice(available_sides)
                        amount = random.uniform(100, 200)
                        meal.append((side_food['id'], amount))
                        current_calories += (amount / 100) * side_food['calories_per_100g']
            
            elif meal_type == 'snack':
                # for snack 1-2 items
                snack_foods = [f for f in foods if any(cat in f.get('food_category', '').lower() for cat in func_categories['items'])]
                if snack_foods:
                    # 1-2 snacks
                    num_snacks = random.randint(1, 2)
                    
                    snack = random.choice(snack_foods)
                    # quantity for snack (30-80g)
                    amount = random.uniform(30, 80)
                    meal.append((snack['id'], amount))
                    current_calories += (amount / 100) * snack['calories_per_100g']
                    
                    if num_snacks == 2:
                        remaining_snacks = [f for f in snack_foods if f['id'] != snack['id']]
                        if remaining_snacks:
                            second_snack = random.choice(remaining_snacks)
                            amount = random.uniform(20, 50)
                            meal.append((second_snack['id'], amount))
                            current_calories += (amount / 100) * second_snack['calories_per_100g']
            
            # adjsut meal portions based on current calories
            if current_calories < 0.7 * target_calories:
                # if we have too few calories, increase portions
                scale_factor = min(1.5, target_calories / max(current_calories, 1))
                meal = [(food_id, amount * scale_factor) for food_id, amount in meal]
            elif current_calories > 1.3 * target_calories:
                # if we have too many calories, reduce portions
                scale_factor = max(0.6, target_calories / max(current_calories, 1))
                meal = [(food_id, amount * scale_factor) for food_id, amount in meal]
            
            population.append(meal)
        
        return population
    
    def _fitness_score(self, meal, foods_dict, target_calories, target_protein, target_carbs, target_fat):
        """Calculate fitness score for a meal based on nutritional accuracy and meal coherence."""
        if not meal:
            return 0.0
        
        conflicting_food_groups = [
        ['yogurt', 'greek yogurt'],                
        ['milk', 'low fat milk', 'skim milk'],       
        ['cheese', 'cottage cheese', 'cream cheese'], 
        ['bread', 'toast', 'bread whole-wheat'],      
        ['chicken', 'chicken breast', 'roasted chicken'],
        ['beef', 'ground beef', 'roasted beef'],      
        ['peanuts', 'peanuts roasted'],               
        ['almonds', 'almonds roasted'],               
        ['rice', 'brown rice', 'wild rice'],           
        ['potato', 'sweet potato', 'mashed potato'] ,
        ['egg', 'egg whole', 'egg white'], 
    ]
            
        # calculate total nutritional values
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # verify food categories
        food_categories = []

        # verify conflicts
        food_names = []
        
        for food_id, amount in meal:
            if food_id not in foods_dict:
                print(f"WARNING: Food ID {food_id} does not exist!")
                continue
                
            food = foods_dict[food_id]
            total_calories += (amount / 100) * food['calories_per_100g']
            total_protein += (amount / 100) * food['protein_per_100g']
            total_carbs += (amount / 100) * food['carbs_per_100g']
            total_fat += (amount / 100) * food['fat_per_100g']
            
            # add category to the list if it exists
            if 'food_category' in food and food['food_category']:
                food_categories.append(food['food_category'].lower())
            
            # add names for conflict verification
            food_names.append(food['name'].lower())
        
        # calculate penalties for nutritional targets
        calorie_penalty = abs(total_calories - target_calories) / max(target_calories, 1)
        protein_penalty = abs(total_protein - target_protein) / max(target_protein, 1)
        carbs_penalty = abs(total_carbs - target_carbs) / max(target_carbs, 1)
        fat_penalty = abs(total_fat - target_fat) / max(target_fat, 1)

        # verify conflicts between food groups
        conflict_penalty = 0.0
        
        for conflict_group in conflicting_food_groups:
            foods_in_group = []
            
            for food_name in food_names:
                for group_item in conflict_group:
                    if group_item.lower() in food_name:
                        foods_in_group.append(group_item)
                        break
            
            # if there are multiple foods from the same group, apply a penalty
            if len(foods_in_group) > 1:
                conflict_penalty += 0.5 * (len(foods_in_group) - 1)
                

        
        # verify coherence of the meal
        coherence_score = 0.0
        
        # verify if meal is a snack or main meal
        if target_calories < 400:
            is_snack = True
        else:
            is_snack = False

        if is_snack:
            # 1. snacks should be simple
            if len(meal) == 2:
                coherence_score += 0.5 
            elif len(meal) == 1:
                coherence_score += 0.4  
            elif len(meal) == 3:
                coherence_score += 0.2  
            else:
                coherence_score -= 0.4 

            unique_categories = len(food_categories)
            # snacks should not be too diverse
            if unique_categories == 2:
                diversity_bonus = 0.3 
            elif unique_categories == 1:
                diversity_bonus = 0.2  
            elif unique_categories == 3:
                diversity_bonus = 0.0 
            else:
                diversity_bonus = -0.2  
        else:
            # 1. main meals should have 2-4 items ideal
            if len(meal) >= 2 and len(meal) <= 4:
                coherence_score += 0.3
            elif len(meal) == 5:
                coherence_score += 0.1
            else:
                coherence_score -= 0.2 
        
            # 2. main meals should have diverse food categories
            unique_categories = set(food_categories)
            if len(unique_categories) >= 3:
                coherence_score += 0.4
            elif len(unique_categories) == 2:
                coherence_score += 0.2
        
        # 3. verify macronutrient balance
        if len(meal) >= 2:
            # Protein should be at least 15% of calories
            protein_ratio = (total_protein * 4) / max(total_calories, 1)
            if protein_ratio >= 0.15:
                coherence_score += 0.2
            
            # penalize if carbs or fat are too low
            if total_carbs < 5:
                coherence_score -= 0.2
            if total_fat < 3:
                coherence_score -= 0.2
        

        # penalize duplicates: more than one food from the same category  (e.g., roasted chicken, grilled chicken)
        from collections import Counter
        category_counts = Counter(food_categories)
        duplicate_penalty = sum((count - 1) * 0.8 for count in category_counts.values() if count > 1)

        # final fitness score calculation
        nutritional_score = 1 / (1 + calorie_penalty * 2 + protein_penalty + carbs_penalty + fat_penalty)
        final_score = nutritional_score * 0.7 + coherence_score * 0.3 - duplicate_penalty - conflict_penalty
        
        return max(0.0,final_score)
    
    def _select_parents(self, population, fitness_scores):
        """Select parents for reproduction using elitism and tournament selection."""
        parents = []
        
        # Elitism - only the best are selected
        elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
        parents.extend([population[i] for i in elite_indices])
        
        # Tournament selection
        while len(parents) < self.population_size:
            # Random selection of candidates for tournament
            tournament_size = 3
            candidates = random.sample(range(len(population)), tournament_size)
            
            # Select the one with the best fitness score
            best_candidate = max(candidates, key=lambda i: fitness_scores[i])
            parents.append(population[best_candidate])
        
        return parents
    
    def _crossover(self, parent1, parent2):
        """Perform crossover between two parent meals to create offspring."""
        if not parent1 or not parent2:
            return parent1 if parent1 else parent2
        
        child = []
        used_food_ids = set()
        
        # add foods from the first parent (with duplicate check)
        for food_id, amount in parent1:
            if random.random() < 0.5 and food_id not in used_food_ids:
                child.append((food_id, amount))
                used_food_ids.add(food_id)
        
        # add foods from the second parent (with duplicate check)
        for food_id, amount in parent2:
            if food_id not in used_food_ids and random.random() < 0.5 and len(child) < 8:
                child.append((food_id, amount))
                used_food_ids.add(food_id)
        
        return child
    
    def _mutate(self, meal, foods_for_meal):
        """Apply random mutations to a meal to introduce genetic variation"""
        if random.random() > self.mutation_rate:
            return meal  # not mutated
        
        mutated_meal = meal.copy()
        
        # Random mutation type
        mutation_type = random.choice(['add', 'remove', 'replace', 'adjust'])
        
        if mutation_type == 'add' and len(mutated_meal) < 8:
            # Random food
            available_foods = [f for f in foods_for_meal if f['id'] not in [food_id for food_id, _ in mutated_meal]]
            if available_foods:
                new_food = random.choice(available_foods)
                amount = random.uniform(20, 100)
                mutated_meal.append((new_food['id'], amount))
                
        elif mutation_type == 'remove' and len(mutated_meal) > 1:
            # remove a random food
            index_to_remove = random.randint(0, len(mutated_meal) - 1)
            mutated_meal.pop(index_to_remove)
            
        elif mutation_type == 'replace' and len(mutated_meal) > 0:
            # replace a random food with another one
            index_to_replace = random.randint(0, len(mutated_meal) - 1)
            food_to_replace = mutated_meal[index_to_replace]
            
            available_foods = [f for f in foods_for_meal if f['id'] not in [food_id for food_id, _ in mutated_meal]]
            if available_foods:
                new_food = random.choice(available_foods)
                amount = random.uniform(20, 100)
                mutated_meal[index_to_replace] = (new_food['id'], amount)
                
        elif mutation_type == 'adjust' and len(mutated_meal) > 0:
            # adjust amount of a random food
            index_to_adjust = random.randint(0, len(mutated_meal) - 1)
            food_id, amount = mutated_meal[index_to_adjust]
            
            new_amount = amount * random.uniform(0.7, 1.3)
            new_amount = max(10, min(200, new_amount))
            mutated_meal[index_to_adjust] = (food_id, new_amount)
        
        return mutated_meal
    
    def _evolve_population(self, population, foods_for_meal, target_calories, target_protein, target_carbs, target_fat):
        """Evolve the population through multiple generations to find optimal meal composition.
        
        Iteratively applies selection, crossover, and mutation operations while
        tracking fitness improvements across generations. Uses elitism to preserve
        best solutions.
        """
        # create a dictionary for fast access to food items by ID
        foods_dict = {food['id']: food for food in foods_for_meal}

        print(f"Foods dict contains {len(foods_dict)} foods")
        if len(foods_dict) == 0:
            print("ERROR: Foods dict is empty!")
            return []
        
        # keep best fitness history for analysis
        best_fitness_history = []
        average_fitness_history = []
        
        for generation in range(self.generations):
            # calculate fitness scores for the current population
            fitness_scores = [
                self._fitness_score(meal, foods_dict, target_calories, target_protein, target_carbs, target_fat)
                for meal in population
            ]
            
            # calculate best and average fitness for this generation
            best_fitness = max(fitness_scores)
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            best_fitness_history.append(best_fitness)
            average_fitness_history.append(avg_fitness)
            
            # print progress every 5 generations
            if generation % 5 == 0 or generation == self.generations - 1: 
                print(f"Gen {generation+1}/{self.generations}: Best fitness = {best_fitness:.4f}, Avg fitness = {avg_fitness:.4f}")
            
            # select parents for the next generation
            parents = self._select_parents(population, fitness_scores)
            
            # create the next generation
            next_generation = []
            
            # elitism
            elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
            next_generation.extend([population[i] for i in elite_indices])
            
            # generate the rest of the next generation
            while len(next_generation) < self.population_size:
                parent1 = random.choice(parents)
                parent2 = random.choice(parents)
                
                child = self._crossover(parent1, parent2)
                
                child = self._mutate(child, foods_for_meal)
                
                if child:  
                    next_generation.append(child)
            
            # update the population for the next generation
            population = next_generation
        
        # evolution results
        print("\nFitness evolution:")
        print(f"Initial fitness: {best_fitness_history[0]:.4f}")
        print(f"Final fitness: {best_fitness_history[-1]:.4f}")
        print(f"Improvement: {(best_fitness_history[-1] - best_fitness_history[0]) / best_fitness_history[0] * 100:.2f}%")
        
        # return best meal from the final population
        fitness_scores = [
        self._fitness_score(meal, foods_dict, target_calories, target_protein, target_carbs, target_fat)
        for meal in population
        ]

        if not fitness_scores:
            print("ERROR: fitness scores are empty!")
            return []
            
        best_index = np.argmax(fitness_scores)
        best_meal = population[best_index]
        
        print(f"Best meal fitness: {fitness_scores[best_index]:.4f}, items: {len(best_meal)}")
        
        if not best_meal:
            print("ATTENTION: Best meal is empty!")
            
        return best_meal