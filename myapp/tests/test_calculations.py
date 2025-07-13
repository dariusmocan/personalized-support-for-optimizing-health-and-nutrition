from django.test import TestCase

class PureCalculationsTest(TestCase):
    """Test mathematical calculations without any database or complex objects"""
    
    def test_bmr_calculation_male(self):
        """Test BMR calculation formula for males"""
        # Mifflin-St Jeor formula: BMR = 10 × weight + 6.25 × height - 5 × age + 5
        
        weight, height, age = 70, 175, 25
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
        
        # Manual calculation: 10*70 + 6.25*175 - 5*25 + 5
        # = 700 + 1093.75 - 125 + 5 = 1673.75
        expected = 700 + 1093.75 - 125 + 5
        self.assertEqual(bmr, expected)
        self.assertEqual(bmr, 1673.75)  # Corectată valoarea
    
    def test_bmr_calculation_female(self):
        """Test BMR calculation formula for females"""
        # Mifflin-St Jeor formula: BMR = 10 × weight + 6.25 × height - 5 × age - 161
        
        weight, height, age = 60, 165, 30
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # Manual calculation: 10*60 + 6.25*165 - 5*30 - 161
        # = 600 + 1031.25 - 150 - 161 = 1320.25
        expected = 600 + 1031.25 - 150 - 161
        self.assertEqual(bmr, expected)
        self.assertEqual(bmr, 1320.25)  # Corectată valoarea
    
    def test_tdee_calculation(self):
        """Test TDEE calculation with activity multipliers"""
        bmr = 1800
        
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        for activity, multiplier in activity_multipliers.items():
            tdee = bmr * multiplier
            
            # TDEE should always be higher than BMR
            self.assertGreater(tdee, bmr)
            
            # Test specific calculations
            if activity == 'sedentary':
                self.assertEqual(tdee, 2160.0)
            elif activity == 'moderate':
                self.assertEqual(tdee, 2790.0)
    
    def test_calorie_adjustment_for_goals(self):
        """Test calorie adjustments for different goals"""
        base_tdee = 2000
        
        # Weight loss: -500 calories (1 lb/week)
        weight_loss = base_tdee - 500
        self.assertEqual(weight_loss, 1500)
        
        # Weight gain: +500 calories (1 lb/week) 
        weight_gain = base_tdee + 500
        self.assertEqual(weight_gain, 2500)
        
        # Maintain weight: no change
        maintain = base_tdee
        self.assertEqual(maintain, 2000)
    
    def test_macro_distribution_calculation(self):
        """Test macronutrient distribution calculations"""
        total_calories = 2000
        
        # Example: 30% protein, 40% carbs, 30% fat
        protein_percent = 0.30
        carbs_percent = 0.40
        fat_percent = 0.30
        
        # Calculate grams (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
        protein_grams = (total_calories * protein_percent) / 4
        carbs_grams = (total_calories * carbs_percent) / 4
        fat_grams = (total_calories * fat_percent) / 9
        
        self.assertEqual(protein_grams, 150.0)
        self.assertEqual(carbs_grams, 200.0)
        self.assertAlmostEqual(fat_grams, 66.67, places=2)
        
        # Verify total calories match
        calculated_calories = (protein_grams * 4) + (carbs_grams * 4) + (fat_grams * 9)
        self.assertAlmostEqual(calculated_calories, total_calories, places=1)
    
    def test_meal_distribution_percentages(self):
        """Test meal calorie distribution"""
        total_calories = 2000
        
        # Folosesc fracții care se adună exact la 1.0
        meal_percentages = {
            'breakfast': 0.25,   # 25%
            'lunch': 0.35,       # 35%
            'dinner': 0.30,      # 30%
            'snack': 0.10        # 10%
        }
        
        # Should sum to 1.0 - folosesc assertAlmostEqual pentru floating point
        total_percentage = sum(meal_percentages.values())
        self.assertAlmostEqual(total_percentage, 1.0, places=10)  # Corectată cu assertAlmostEqual
        
        # Calculate actual calories per meal
        for meal, percentage in meal_percentages.items():
            calories = total_calories * percentage
            
            if meal == 'breakfast':
                self.assertEqual(calories, 500)
            elif meal == 'lunch':
                self.assertEqual(calories, 700)
            elif meal == 'dinner':
                self.assertEqual(calories, 600)
            elif meal == 'snack':
                self.assertEqual(calories, 200)
    
    def test_nutrition_scaling(self):
        """Test nutrition scaling for different portions"""
        # Base nutrition per 100g
        base_calories = 100
        base_protein = 20
        base_carbs = 15
        base_fat = 5
        
        # Test different portion sizes
        portions = [50, 150, 200, 75]
        
        for portion in portions:
            scale_factor = portion / 100
            
            scaled_calories = base_calories * scale_factor
            scaled_protein = base_protein * scale_factor
            scaled_carbs = base_carbs * scale_factor
            scaled_fat = base_fat * scale_factor
            
            # Verify scaling is proportional
            self.assertEqual(scaled_calories, base_calories * portion / 100)
            self.assertEqual(scaled_protein, base_protein * portion / 100)
            self.assertEqual(scaled_carbs, base_carbs * portion / 100)
            self.assertEqual(scaled_fat, base_fat * portion / 100)
    
    def test_bmr_edge_cases(self):
        """Test BMR calculation with edge cases"""
        # Very young adult
        young_male_bmr = 10 * 60 + 6.25 * 170 - 5 * 18 + 5
        expected_young = 600 + 1062.5 - 90 + 5
        self.assertEqual(young_male_bmr, expected_young)
        self.assertEqual(young_male_bmr, 1577.5)
        
        # Older adult
        older_female_bmr = 10 * 55 + 6.25 * 160 - 5 * 65 - 161
        expected_older = 550 + 1000 - 325 - 161
        self.assertEqual(older_female_bmr, expected_older)
        self.assertEqual(older_female_bmr, 1064.0)
        
    def test_percentage_to_decimal_conversion(self):
        """Test percentage conversions"""
        # Test common percentages
        test_cases = [
            (25, 0.25),
            (50, 0.50),
            (100, 1.0),
            (33.33, 0.3333),
            (66.67, 0.6667)
        ]
        
        for percentage, expected_decimal in test_cases:
            decimal = percentage / 100
            self.assertAlmostEqual(decimal, expected_decimal, places=4)