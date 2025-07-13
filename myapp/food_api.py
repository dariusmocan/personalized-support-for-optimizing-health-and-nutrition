import requests
import os
import json
from django.conf import settings
from functools import lru_cache

API_KEY = getattr(settings, 'USDA_API_KEY', os.environ.get('USDA_API_KEY'))



class FoodAPIClient:
    """Client for interacting with USDA FoodData Central API"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1/"

    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("API key for USDA FoodData Central API has not been configured.")
    
    @lru_cache(maxsize=128)
    def search_foods(self, query, page_size=50, page_number=1, data_types=None):
        """
        Search for foods by a search term
        
        Args:
            query (str): The search term
            page_size (int): Number of results per page
            page_number (int): Page number
            data_types (str or list): Data types to include
        
        Returns:
            dict: Search results
        """
        endpoint = f"{self.BASE_URL}foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        
        # Adăugăm dataType direct în parametri, dacă este specificat
        if data_types:
            if isinstance(data_types, list):
                params["dataType"] = ",".join(data_types)
            else:
                params["dataType"] = data_types
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        
        return response.json()
    
    @lru_cache(maxsize=256)
    def get_food_details(self, food_id):
        """
        Get complete details about a specific food
        
        Args:
            food_id (str): The food ID
        
        Returns:
            dict: Food details
        """
        endpoint = f"{self.BASE_URL}food/{food_id}"
        params = {"api_key": self.api_key}
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_nutrient_info(self, food_data, nutrient_ids):
        """
        Extract information about specific nutrients from a food
        
        Args:
            food_data (dict): Food data
            nutrient_ids (dict): Dictionary with nutrient_name: nutrient_id mappings
        
        Returns:
            dict: Information about specified nutrients
        """
        nutrients = {}
        
        if 'foodNutrients' in food_data:
            for nutrient in food_data['foodNutrients']:
                nutrient_id = nutrient.get('nutrientId') or nutrient.get('nutrient', {}).get('id')
                if nutrient_id:
                    for name, id_list in nutrient_ids.items():
                        if nutrient_id in id_list:
                            amount = nutrient.get('amount') or nutrient.get('value', 0)
                            unit = nutrient.get('unitName') or nutrient.get('nutrient', {}).get('unitName', '')
                            nutrients[name] = {
                                'amount': amount,
                                'unit': unit
                            }
        
        return nutrients