from django.test import TestCase

class UtilityFunctionsTest(TestCase):
    """Test utility functions and helpers"""
    
    def test_percentage_calculation(self):
        """Test percentage calculations"""
        # Test basic percentage
        result = (75 / 100) * 50
        self.assertEqual(result, 37.5)
        
        # Test percentage of total
        part = 250
        total = 2000
        percentage = (part / total) * 100
        self.assertEqual(percentage, 12.5)
    
    def test_rounding_functions(self):
        """Test various rounding scenarios"""
        values = [
            (123.456, 2, 123.46),
            (123.454, 2, 123.45),
            (100.0, 1, 100.0),
            (99.99, 0, 100),
        ]
        
        for value, places, expected in values:
            result = round(value, places)
            self.assertEqual(result, expected)
    
    def test_range_checking(self):
        """Test if values are within expected ranges"""
        def is_in_range(value, min_val, max_val):
            return min_val <= value <= max_val
        
        # Test cases
        self.assertTrue(is_in_range(50, 0, 100))
        self.assertTrue(is_in_range(0, 0, 100))
        self.assertTrue(is_in_range(100, 0, 100))
        self.assertFalse(is_in_range(-1, 0, 100))
        self.assertFalse(is_in_range(101, 0, 100))
    
    def test_list_operations(self):
        """Test common list operations used in algorithm"""
        test_list = [(1, 100), (2, 150), (3, 200)]
        
        # Extract first elements (food IDs)
        food_ids = [item[0] for item in test_list]
        self.assertEqual(food_ids, [1, 2, 3])
        
        # Extract second elements (amounts)
        amounts = [item[1] for item in test_list]
        self.assertEqual(amounts, [100, 150, 200])
        
        # Check for duplicates
        has_duplicates = len(food_ids) != len(set(food_ids))
        self.assertFalse(has_duplicates)
        
        # Test with duplicates
        duplicate_list = [(1, 100), (2, 150), (1, 200)]
        duplicate_ids = [item[0] for item in duplicate_list]
        has_duplicates = len(duplicate_ids) != len(set(duplicate_ids))
        self.assertTrue(has_duplicates)
    
    def test_error_calculation(self):
        """Test error/difference calculations"""
        def calculate_error(target, actual):
            if target == 0:
                return abs(actual)
            return abs(target - actual) / target
        
        # Perfect match
        error1 = calculate_error(100, 100)
        self.assertEqual(error1, 0.0)
        
        # 10% over
        error2 = calculate_error(100, 110)
        self.assertEqual(error2, 0.1)
        
        # 20% under
        error3 = calculate_error(100, 80)
        self.assertEqual(error3, 0.2)
        
        # Zero target
        error4 = calculate_error(0, 50)
        self.assertEqual(error4, 50)
    
    def test_weighted_average(self):
        """Test weighted average calculations"""
        values = [100, 200, 300]
        weights = [0.3, 0.5, 0.2]
        
        # Manual calculation
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        total_weight = sum(weights)
        weighted_avg = weighted_sum / total_weight
        
        expected = (100 * 0.3 + 200 * 0.5 + 300 * 0.2) / 1.0
        self.assertEqual(weighted_avg, expected)
        self.assertEqual(weighted_avg, 190.0)