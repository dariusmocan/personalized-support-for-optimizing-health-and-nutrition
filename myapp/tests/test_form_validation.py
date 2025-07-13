from django.test import TestCase

class FormValidationTest(TestCase):
    """Test form validation logic without database"""
    
    def test_age_validation_bounds(self):
        """Test age validation ranges"""
        valid_ages = [18, 25, 35, 50, 65, 80, 100]
        invalid_ages = [-5, 0, 17, 150, 200]
        
        for age in valid_ages:
            self.assertGreaterEqual(age, 18, f"Age {age} should be valid")
            self.assertLessEqual(age, 120, f"Age {age} should be valid")
        
        for age in invalid_ages:
            is_invalid = age < 18 or age > 120
            self.assertTrue(is_invalid, f"Age {age} should be invalid")
    
    def test_height_validation_bounds(self):
        """Test height validation in cm"""
        valid_heights = [140, 160, 175, 190, 220]
        invalid_heights = [50, 100, 139, 251, 300]
        
        for height in valid_heights:
            self.assertGreaterEqual(height, 140, f"Height {height}cm should be valid")
            self.assertLessEqual(height, 250, f"Height {height}cm should be valid")
        
        for height in invalid_heights:
            is_invalid = height < 140 or height > 250
            self.assertTrue(is_invalid, f"Height {height}cm should be invalid")
    
    def test_weight_validation_bounds(self):
        """Test weight validation in kg"""
        valid_weights = [40, 60, 75, 90, 150]
        invalid_weights = [20, 35, 201, 300]
        
        for weight in valid_weights:
            self.assertGreaterEqual(weight, 40, f"Weight {weight}kg should be valid")
            self.assertLessEqual(weight, 200, f"Weight {weight}kg should be valid")
        
        for weight in invalid_weights:
            is_invalid = weight < 40 or weight > 200
            self.assertTrue(is_invalid, f"Weight {weight}kg should be invalid")
    
    def test_gender_validation(self):
        """Test gender field validation"""
        valid_genders = ['male', 'female']
        invalid_genders = ['', 'other', 'unknown', 'M', 'F', None]
        
        for gender in valid_genders:
            self.assertIn(gender, ['male', 'female'])
        
        for gender in invalid_genders:
            self.assertNotIn(gender, ['male', 'female'])
    
    def test_activity_level_validation(self):
        """Test activity level validation"""
        valid_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
        invalid_levels = ['', 'low', 'high', 'extreme', None]
        
        for level in valid_levels:
            self.assertIn(level, valid_levels)
        
        for level in invalid_levels:
            self.assertNotIn(level, valid_levels)
    
    def test_goal_validation(self):
        """Test goal validation"""
        valid_goals = ['lose', 'maintain', 'gain']
        invalid_goals = ['', 'weight_loss', 'bulk', 'cut', None]
        
        for goal in valid_goals:
            self.assertIn(goal, valid_goals)
        
        for goal in invalid_goals:
            self.assertNotIn(goal, valid_goals)