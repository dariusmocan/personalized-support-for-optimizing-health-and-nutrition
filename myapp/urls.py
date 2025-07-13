from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", views.home, name="home"),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('quiz/',views.quiz_view, name='quiz_view'),
    path('results/',views.results_view, name='results_view'),  

    path('meal-plan/', views.create_view_meal_plan, name='meal_plan'),
    
    path('meal-plan/<int:plan_id>/', views.view_meal_plan, name='view_meal_plan'),
    path('debug-meal-plan/<int:plan_id>/', views.debug_meal_plan, name='debug_meal_plan'),

    path('food-journal/', views.food_journal, name='food_journal'),
    path('api/search-foods/', views.search_foods, name='search_foods'),
    path('api/add-food/', views.add_food_to_journal, name='add_food_to_journal'),
    path('api/delete-food/<int:entry_id>/', views.delete_food_from_journal, name='delete_food_from_journal'),


    path('service-worker.js', 
         TemplateView.as_view(
             template_name="service-worker.js", 
             content_type='application/javascript'
         ),
         name='service-worker.js'),
         
    path('manifest.json',
         TemplateView.as_view(
             template_name="manifest.json",
             content_type='application/json'
         ),
         name='manifest.json'),

    path('favicon.ico', 
         RedirectView.as_view(url=staticfiles_storage.url('images/favicon.ico'))),
]