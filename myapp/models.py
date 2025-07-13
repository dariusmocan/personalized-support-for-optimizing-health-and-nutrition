from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, make_password
import uuid, datetime
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import get_user_model


class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100) 
    email = models.EmailField(unique=True)  
    password = models.CharField(max_length=128) 

    def __str__(self):
        return self.name


class QuizResponse(models.Model):
    OBJECTIVE_CHOICES = [
        (1, 'Weight loss'),
        (2, 'Weight gain'),
        (3, 'Muscle growth'),
        (4, 'Body recomposition')
    ]

    ACTIVITY_LEVEL_CHOICES = [
        (1, 'Sedentary (minimal activity, desk job)'),
        (2, 'Lightly active (light exercises 1-3 days/week)'),
        (3, 'Moderately active (moderate exercises 3-5 days/week)'),
        (4, 'Very active (intense exercises 6-7 days/week)'),
        (5, 'Extremely active (intense daily exercises, physical job or 2x/day training)')
    ]
    
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE) 
    age = models.PositiveIntegerField()
    height = models.PositiveIntegerField(help_text="In cm")
    weight = models.FloatField(help_text="In kg")
    gender = models.CharField(max_length=10, choices=[('masculin', 'Masculin'), ('feminin', 'Feminin')])
    objective = models.IntegerField(choices=OBJECTIVE_CHOICES)
    activity_level = models.IntegerField(choices=ACTIVITY_LEVEL_CHOICES, default=1)
    bmr = models.FloatField(null=True, blank=True)  
    tdee = models.FloatField(null=True, blank=True) 

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s responses ({self.submitted_at.strftime('%Y-%m-%d')})"
    
    def calculate_bmr(self):
        """using Mifflin-St Jeor formula"""
        if self.gender == 'masculin':
            self.bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            self.bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return self.bmr
    
    def calculate_tdee(self):
        if not self.bmr:
            self.calculate_bmr()
            
        activity_multipliers = {
            1: 1.2,    # Sedentary
            2: 1.375,  # Lightly active
            3: 1.55,   # Moderately active
            4: 1.725,  # Very active
            5: 1.9     # Extremely active
        }
        
        self.tdee = self.bmr * activity_multipliers[self.activity_level]
        return self.tdee
    
    def calculate_target_calories(self):
        if not self.tdee:
            self.calculate_tdee()
            
        if self.objective == 1:  # weight loss
            self.target_calories = self.tdee - 500  
        elif self.objective == 2:  # weight gain
            self.target_calories = self.tdee + 500  
        elif self.objective == 3:  # muscle growth
            self.target_calories = self.tdee + 300  
        elif self.objective == 4:  # body recomposition
            self.target_calories = self.tdee  
            
        return self.target_calories
    
class Food(models.Model):
    """Represents a food item with nutritional information"""
    fdc_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    calories_per_100g = models.FloatField()
    protein_per_100g = models.FloatField()
    carbs_per_100g = models.FloatField() 
    fat_per_100g = models.FloatField()
    food_category = models.CharField(max_length=100, null=True, blank=True)
    serving_size = models.FloatField(default=100.0)  
    serving_unit = models.CharField(max_length=20, default="g")
    
    def __str__(self):
        return self.name

    @property
    def macronutrient_ratio(self):
        total_calories = self.calories_per_100g
        if total_calories == 0:
            return (0, 0, 0)
            
        protein_cals = self.protein_per_100g * 4
        carbs_cals = self.carbs_per_100g * 4
        fat_cals = self.fat_per_100g * 9
        
        protein_pct = protein_cals / total_calories
        carbs_pct = carbs_cals / total_calories
        fat_pct = fat_cals / total_calories
        
        return (protein_pct, carbs_pct, fat_pct)


class MealPlan(models.Model):
    """Represents a user's meal plan"""
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    target_calories = models.FloatField()
    target_protein = models.FloatField() 
    target_carbs = models.FloatField()   
    target_fat = models.FloatField()     
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Plan for {self.user.username}: {self.name}"


class MealPlanDay(models.Model):
    """Represents a day in a meal plan"""
    DAYS_OF_WEEK = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday')
    ]
    
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='days')
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    
    class Meta:
        unique_together = ('meal_plan', 'day')
    
    def __str__(self):
        return f"{self.meal_plan.name} - {self.get_day_display()}"


class Meal(models.Model):
    """Represents a meal in a specific day of the meal plan"""
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack')
    ]
    
    meal_plan_day = models.ForeignKey(MealPlanDay, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    
    def __str__(self):
        return f"{self.meal_plan_day} - {self.get_meal_type_display()}"
    
    @property
    def total_calories(self):
        return sum(item.calories for item in self.food_items.all())
    
    @property
    def total_protein(self):
        return sum(item.protein for item in self.food_items.all())
    
    @property
    def total_carbs(self):
        return sum(item.carbs for item in self.food_items.all())
    
    @property
    def total_fat(self):
        return sum(item.fat for item in self.food_items.all())


class MealFoodItem(models.Model):
    """A specific food item in a meal"""
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='food_items')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    amount = models.FloatField(help_text="Gramaj")
    
    def __str__(self):
        return f"{self.amount}g {self.food.name}"
    
    @property
    def calories(self):
        return (self.amount / 100) * self.food.calories_per_100g
    
    @property
    def protein(self):
        return (self.amount / 100) * self.food.protein_per_100g
    
    @property
    def carbs(self):
        return (self.amount / 100) * self.food.carbs_per_100g
    
    @property
    def fat(self):
        return (self.amount / 100) * self.food.fat_per_100g
    
class FoodJournal(models.Model):
    """Model for a user's food journal entry"""
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='journal_entries')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    amount = models.FloatField(help_text="Amount in grams")
    meal_type = models.CharField(max_length=20, choices=Meal.MEAL_TYPES, default='snack')
    time_consumed = models.TimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.amount}g of {self.food.name} on {self.date}"
    
    @property
    def calories(self):
        return (self.amount / 100) * self.food.calories_per_100g
    
    @property
    def protein(self):
        return (self.amount / 100) * self.food.protein_per_100g
    
    @property
    def carbs(self):
        return (self.amount / 100) * self.food.carbs_per_100g
    
    @property
    def fat(self):
        return (self.amount / 100) * self.food.fat_per_100g