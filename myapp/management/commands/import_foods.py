import os
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from myapp.food_api import FoodAPIClient
from myapp.models import Food

class Command(BaseCommand):
    help = 'Import foods from USDA FoodData Central API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queries',
            nargs='+',
            type=str,
            help='List of search terms for foods',
            default=[
                
                'apple', 'banana', 'chicken', 'beef', 'rice', 'potato', 'egg',
                'milk', 'cheese', 'yogurt', 'bread', 'pasta', 'fish', 'salmon',
                'olive oil', 'butter', 'broccoli', 'spinach', 'carrot', 'tomato',
                'avocado', 'nuts', 'beans', 'lentils', 'quinoa', 'oats',
                
                'pizza', 'lasagna', 'stew beef', 'chicken soup', 'pasta salad',
                'chicken with rice', 'vegetable curry', 'chicken casserole',
                'beef stir fry', 'burrito', 'sandwich', 'taco', 'hamburger',
                'fish with potatoes', 'omelette', 'risotto', 'spaghetti bolognese',
                
                'cereal breakfast', 'pancakes', 'waffles', 'french toast', 'breakfast sandwich',
                'breakfast burrito', 'oatmeal', 'smoothie bowl', 'granola',
                
                'lunch bowl', 'salad with chicken', 'soup vegetable', 'meal prep bowl',
                'buddha bowl', 'rice bowl', 'sandwich lunch', 'wrap', 'pasta dish',
                
                'dinner plate', 'fish dinner', 'steak dinner', 'roast dinner',
                'chicken dinner', 'pasta dinner', 'vegetarian dinner', 'vegan meal',
                
                'snack bar', 'trail mix', 'protein bar', 'energy ball',
                'fruit cup', 'vegetable snack', 'hummus with carrot', 'yogurt parfait'
            ]
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of foods per search',
            default=10
        )

        parser.add_argument(
        '--data-types',
        nargs='+',
        type=str,
        help='Data types to include (e.g., Foundation SR Legacy Survey)',
        default=['Foundation', 'SR Legacy', 'Survey (FNDDS)']
        )
    
    def is_edible_food(self, food_name):
        """Determines if the food appears to be directly edible"""

        negative_keywords = [
            'crude', 'uncooked', 'unprepared', 'dry mix',
            'concentrate', 'infant formula', 'additive'
        ]
        
        animal_products = [
        'chicken', 'beef', 'pork', 'meat', 'turkey', 'fish', 'salmon', 
        'tuna', 'lamb', 'duck', 'goose', 'seafood', 'shrimp', 'eggs', 'rice',
        'milk', 'cheese', 'yogurt', 'butter', 'cream', 'lard', 'gelatin',
        ]
        
        food_name_lower = food_name.lower()
        
        if 'raw' in food_name_lower:
            for product in animal_products:
                if product in food_name_lower:
                    return False
        
        for keyword in negative_keywords:
            if keyword in food_name_lower:
                return False
        
        return True

    def get_food_category(self, query):
        """Extract category by removing the part after the last comma"""
        # delete anything after the comma, generalisation for the categories
        if ',' in query:
            return query.split(',')[0].strip().lower()
        else:
            return query.lower()
    
    def handle(self, *args, **options):
        queries = options['queries']
        limit = options['limit']
        data_types = options['data_types']
        self.stdout.write(f"Searching foods only for category: {', '.join(data_types)}")

        client = FoodAPIClient()
        
        # calories and macronutrients IDs
        nutrient_ids = {
            'calories': [1008, 208],  
            'protein': [1003, 203],   
            'carbs': [1005, 205],     
            'fat': [1004, 204]        
        }
        
        total_imported = 0
        
        for query in queries:
            category = self.get_food_category(query)
            self.stdout.write(f"Importing foods for: '{query}'")
            try:
                search_results = client.search_foods(
                query, 
                page_size=limit,
                data_types=",".join(data_types)
                )
                
                if 'foods' not in search_results:
                    self.stdout.write(self.style.WARNING(f"No results for '{query}'"))
                    continue
                
                for food_item in search_results['foods']:
                    fdc_id = food_item.get('fdcId')
                    food_name = food_item.get('description', '')

                    if Food.objects.filter(fdc_id=fdc_id).exists():
                        self.stdout.write(f"Food {food_item['description']} already exists.")
                        continue

                    if not self.is_edible_food(food_name):
                        self.stdout.write(f"Skipping non-edible food: {food_name}")
                        continue

                    try:
                        food_details = client.get_food_details(fdc_id)
                        
                        nutrients = client.get_nutrient_info(food_details, nutrient_ids)
                        
                        if not all(key in nutrients for key in ['calories', 'protein', 'carbs', 'fat']):
                            self.stdout.write(f"Missing nutritional data for {food_item['description']}")
                            continue
                        
                        food = Food(
                            fdc_id=fdc_id,
                            name=food_item.get('description', ''),
                            description=food_item.get('additionalDescriptions', ''),
                            calories_per_100g=nutrients['calories']['amount'],
                            protein_per_100g=nutrients['protein']['amount'],
                            carbs_per_100g=nutrients['carbs']['amount'],
                            fat_per_100g=nutrients['fat']['amount'],
                            food_category=category
                        )
                        food.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"Imported: {food.name}"))
                        total_imported += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing {food_item.get('description')}: {str(e)}"))
                    
                    time.sleep(0.5)
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error searching '{query}': {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"Import completed. {total_imported} foods imported."))