from django.contrib import admin
from .models import User
from .models import QuizResponse, Food, MealPlan, MealPlanDay, Meal, MealFoodItem, FoodJournal
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email')  
    search_fields = ('name', 'email')  

@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'height', 'weight', 'gender', 'objective', 'submitted_at') 
    list_filter = ('gender', 'objective') 
    search_fields = ('user_username', 'age', 'height', 'weight') 

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g', 'food_category')
    list_filter = ('food_category',)
    search_fields = ('name', 'description', 'food_category')

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'user', 'target_calories', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'user__username')

@admin.register(MealPlanDay)
class MealPlanDayAdmin(admin.ModelAdmin):
    list_display = ('meal_plan', 'get_day_display')
    list_filter = ('day',)
    search_fields = ('meal_plan__name',)

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('get_meal_type_display', 'meal_plan_day', 'total_calories', 'total_protein', 'total_carbs', 'total_fat')
    list_filter = ('meal_type',)
    search_fields = ('meal_plan_day__meal_plan__name',)

@admin.register(MealFoodItem)
class MealFoodItemAdmin(admin.ModelAdmin):
    list_display = ('food', 'meal', 'amount', 'calories', 'protein', 'carbs', 'fat')
    search_fields = ('food__name', 'meal__meal_plan_day__meal_plan__name')

@admin.register(FoodJournal)
class FoodJournalAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    list_filter = ('date', 'meal_type')
    search_fields = ('user__username', 'food_item__name')