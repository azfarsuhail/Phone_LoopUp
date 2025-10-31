# tests/test_phone_lookup.py
import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock
import json

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from modules.phone_lookup import PhoneLookup, validate_phone_number, batch_lookup_numbers
from modules.usage_tracker import UsageTracker


class TestPhoneLookup(unittest.TestCase):
    """Test cases for PhoneLookup class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.phone_lookup = PhoneLookup()
        self.test_input_file = Path(__file__).parent / "test_data" / "test_numbers.xlsx"
        self.test_output_file = Path(tempfile.mktemp(suffix=".xlsx"))
        
        # Create test data directory
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create test Excel file
        self._create_test_excel_file()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test output file if it exists
        if self.test_output_file.exists():
            self.test_output_file.unlink()
        
        # Remove test input file if it was created
        if hasattr(self, '_created_test_file') and self._created_test_file:
            if self.test_input_file.exists():
                self.test_input_file.unlink()
    
    def _create_test_excel_file(self):
        """Create a test Excel file with sample phone numbers."""
        test_data = {
            'Number': [
                '923001234567',    # Valid Pakistani number
                '03001234567',     # Valid Pakistani number with 0
                '+923001234568',   # Valid Pakistani number with +
                '12345',           # Invalid: too short
                'abc123',          # Invalid: contains letters
                '',                # Invalid: empty
                '923001234569',    # Another valid number
            ]
        }
        df = pd.DataFrame(test_data)
        df.to_excel(self.test_input_file, index=False)
        self._created_test_file = True
    
    def test_initialization(self):
        """Test that PhoneLookup initializes correctly."""
        self.assertIsInstance(self.phone_lookup, PhoneLookup)
        self.assertFalse(self.phone_lookup.is_running)
        self.assertEqual(self.phone_lookup.processed_count, 0)
        self.assertEqual(self.phone_lookup.error_count, 0)
    
    def test_configure(self):
        """Test configuration of PhoneLookup."""
        config = {
            'input_file': str(self.test_input_file),
            'output_file': str(self.test_output_file),
            'api_key': 'test_api_key_123',
            'api_host': 'eyecon.p.rapidapi.com',
            'delay': 1.0,
            'save_interval': 5,
            'max_retries': 3,
            'timeout': 30
        }
        
        # Configure with minimal parameters
        self.phone_lookup.configure(
            input_file=config['input_file'],
            output_file=config['output_file'],
            api_key=config['api_key']
        )
        
        # Check configuration
        self.assertEqual(self.phone_lookup.config['input_file'], config['input_file'])
        self.assertEqual(self.phone_lookup.config['output_file'], config['output_file'])
        self.assertEqual(self.phone_lookup.config['api_key'], config['api_key'])
        self.assertEqual(self.phone_lookup.config['api_host'], 'eyecon.p.rapidapi.com')
        self.assertEqual(self.phone_lookup.config['delay'], 1.5)  # Default value
    
    def test_configure_with_callbacks(self):
        """Test configuration with callbacks."""
        mock_log = Mock()
        mock_status = Mock()
        mock_progress = Mock()
        mock_usage = Mock()
        mock_stop = Mock(return_value=False)
        
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key',
            log_callback=mock_log,
            status_callback=mock_status,
            progress_callback=mock_progress,
            usage_callback=mock_usage,
            stop_callback=mock_stop
        )
        
        # Test callbacks are set
        self.assertEqual(self.phone_lookup.callbacks['log'], mock_log)
        self.assertEqual(self.phone_lookup.callbacks['status'], mock_status)
        self.assertEqual(self.phone_lookup.callbacks['progress'], mock_progress)
        self.assertEqual(self.phone_lookup.callbacks['usage'], mock_usage)
        self.assertEqual(self.phone_lookup.callbacks['stop'], mock_stop)
        
        # Test stop callback
        self.assertFalse(self.phone_lookup.should_stop())
        mock_stop.assert_called_once()
    
    @patch('modules.phone_lookup.requests.Session')
    def test_api_request_retry_logic(self, mock_session):
        """Test API request retry logic."""
        # Mock session and response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "status": True,
            "data": {"fullName": "Test User"}
        }
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Configure phone lookup
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key',
            max_retries=2
        )
        
        # Test successful request
        params = {"code": "92", "number": "3001234567"}
        response = self.phone_lookup._make_api_request(params)
        
        self.assertIsNotNone(response)
        mock_session_instance.get.assert_called_once()
    
    @patch('modules.phone_lookup.requests.Session')
    def test_api_request_timeout(self, mock_session):
        """Test API request timeout handling."""
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = Exception("Timeout")
        mock_session.return_value = mock_session_instance
        
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key',
            max_retries=1
        )
        
        params = {"code": "92", "number": "3001234567"}
        response = self.phone_lookup._make_api_request(params)
        
        self.assertIsNone(response)
        self.assertEqual(mock_session_instance.get.call_count, 1)
    
    def test_parse_phone_number(self):
        """Test phone number parsing."""
        test_cases = [
            # (input, expected_country_code, expected_local_number)
            ('923001234567', '92', '3001234567'),
            ('03001234567', '92', '3001234567'),
            ('+923001234567', '92', '3001234567'),
            ('3001234567', '92', '3001234567'),  # No country code
            ('92300123456789', '92', '300123456789'),  # Longer number
        ]
        
        for number, expected_code, expected_local in test_cases:
            with self.subTest(number=number):
                country_code, local_number = self.phone_lookup._parse_phone_number(number)
                self.assertEqual(country_code, expected_code)
                self.assertEqual(local_number, expected_local)
    
    def test_extract_api_data(self):
        """Test API data extraction."""
        # Test data with multiple name types and images
        api_data = {
            "fullName": "John Doe",
            "otherNames": [
                {"name": "Johnny"},
                "John D",
                {"name": "JD"}
            ],
            "image": "http://example.com/image1.jpg",
            "images": [
                {
                    "pictures": {
                        "200": "http://example.com/image2_200.jpg",
                        "600": "http://example.com/image2_600.jpg"
                    }
                }
            ],
            "b64": "base64_encoded_image_data"
        }
        
        result = self.phone_lookup._extract_api_data(api_data)
        
        # Check names
        self.assertEqual(result["full_name"], "John Doe")
        self.assertIn("Johnny", result["other_names"])
        self.assertIn("John D", result["other_names"])
        self.assertIn("JD", result["other_names"])
        
        # Check images
        self.assertIn("http://example.com/image1.jpg", result["image_urls"])
        # Should only include the largest image from pictures
        self.assertIn("http://example.com/image2_600.jpg", result["image_urls"])
        self.assertNotIn("http://example.com/image2_200.jpg", result["image_urls"])
        
        # Check base64
        self.assertIn("base64_encoded_image_data", result["base64_images"])
    
    def test_extract_api_data_list(self):
        """Test API data extraction from list."""
        api_data = [
            {
                "fullName": "User One",
                "image": "http://example.com/user1.jpg"
            },
            {
                "fullName": "User Two", 
                "image": "http://example.com/user2.jpg"
            }
        ]
        
        result = self.phone_lookup._extract_api_data(api_data)
        
        self.assertEqual(result["full_name"], "User One")  # First entry
        self.assertIn("http://example.com/user1.jpg", result["image_urls"])
        self.assertIn("http://example.com/user2.jpg", result["image_urls"])
    
    def test_clean_phone_numbers(self):
        """Test phone number cleaning and validation."""
        test_data = {
            'Number': [
                '923001234567',      # Valid
                '03001234567',       # Valid with 0
                '12345',             # Invalid: too short
                'abc123',            # Invalid: letters
                '',                  # Invalid: empty
                '+92 300 123 4567',  # Valid with spaces and +
            ]
        }
        df = pd.DataFrame(test_data)
        
        # Mock the _clean_phone_numbers method call
        cleaned_df = self.phone_lookup._clean_phone_numbers(df)
        
        # Should only keep valid numbers
        self.assertEqual(len(cleaned_df), 3)  # 3 valid numbers
        self.assertIn('Cleaned_Number', cleaned_df.columns)
        
        # Check that valid numbers are preserved
        valid_numbers = ['923001234567', '923001234567', '923001234567']
        for num in cleaned_df['Cleaned_Number']:
            self.assertIn(num, valid_numbers)
    
    @patch('modules.phone_lookup.PhoneLookup._make_api_request')
    def test_lookup_phone_number_success(self, mock_api_request):
        """Test successful phone number lookup."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "fullName": "Test User",
                "otherNames": ["Test", "User"],
                "image": "http://example.com/test.jpg",
                "b64": "base64_data"
            }
        }
        mock_api_request.return_value = mock_response
        
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key'
        )
        
        result = self.phone_lookup._lookup_phone_number('923001234567')
        
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["full_name"], "Test User")
        self.assertEqual(result["other_names"], ["Test", "User"])
        self.assertEqual(result["image_urls"], ["http://example.com/test.jpg"])
        self.assertEqual(result["base64_images"], ["base64_data"])
    
    @patch('modules.phone_lookup.PhoneLookup._make_api_request')
    def test_lookup_phone_number_api_error(self, mock_api_request):
        """Test phone number lookup with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": False,
            "message": "API error message"
        }
        mock_api_request.return_value = mock_response
        
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key'
        )
        
        result = self.phone_lookup._lookup_phone_number('923001234567')
        
        self.assertEqual(result["status"], "API Error: API error message")
        self.assertEqual(result["full_name"], "")
        self.assertEqual(result["error_message"], "API error message")
    
    @patch('modules.phone_lookup.PhoneLookup._make_api_request')
    def test_lookup_phone_number_network_error(self, mock_api_request):
        """Test phone number lookup with network error."""
        mock_api_request.return_value = None  # Simulate failed request
        
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key'
        )
        
        result = self.phone_lookup._lookup_phone_number('923001234567')
        
        self.assertEqual(result["status"], "API Error")
        self.assertEqual(result["error_message"], "Request failed after retries")
    
    def test_initialize_results_df(self):
        """Test results dataframe initialization."""
        input_data = {
            'Number': ['923001234567', '923001234568'],
            'Other_Column': ['A', 'B']
        }
        df = pd.DataFrame(input_data)
        
        results_df = self.phone_lookup._initialize_results_df(df)
        
        # Check that original columns are preserved
        self.assertIn('Number', results_df.columns)
        self.assertIn('Other_Column', results_df.columns)
        
        # Check that result columns are added
        expected_columns = [
            'Lookup_Status', 'Full_Name', 'Other_Names', 
            'Image_URLs', 'Base64_Images', 'Lookup_Timestamp', 'Error_Message'
        ]
        for col in expected_columns:
            self.assertIn(col, results_df.columns)
    
    def test_update_results(self):
        """Test updating results dataframe."""
        # Create a test dataframe
        test_data = {
            'Number': ['923001234567'],
            'Lookup_Status': [''],
            'Full_Name': ['']
        }
        self.phone_lookup.current_df = pd.DataFrame(test_data)
        
        # Test result data
        result = {
            'status': 'Success',
            'full_name': 'Test User',
            'other_names': ['User', 'Test'],
            'image_urls': ['img1.jpg'],
            'base64_images': ['b64_data'],
            'timestamp': '2024-01-01T10:00:00',
            'error_message': ''
        }
        
        self.phone_lookup._update_results(0, result)
        
        # Check that values are updated
        self.assertEqual(self.phone_lookup.current_df.at[0, 'Lookup_Status'], 'Success')
        self.assertEqual(self.phone_lookup.current_df.at[0, 'Full_Name'], 'Test User')
        self.assertEqual(self.phone_lookup.current_df.at[0, 'Other_Names'], 'User | Test')
        self.assertEqual(self.phone_lookup.current_df.at[0, 'Image_URLs'], 'img1.jpg')
        self.assertEqual(self.phone_lookup.current_df.at[0, 'Base64_Images'], 'b64_data')
    
    def test_save_results(self):
        """Test saving results to Excel file."""
        # Create test results dataframe
        test_data = {
            'Number': ['923001234567', '923001234568'],
            'Lookup_Status': ['Success', 'Error'],
            'Full_Name': ['User One', ''],
            'Cleaned_Number': ['923001234567', '923001234568']
        }
        self.phone_lookup.current_df = pd.DataFrame(test_data)
        self.phone_lookup.config = {'output_file': str(self.test_output_file)}
        
        # Test saving
        self.phone_lookup._save_results()
        
        # Check that file was created
        self.assertTrue(self.test_output_file.exists())
        
        # Check that file can be read and has correct data
        saved_df = pd.read_excel(self.test_output_file)
        self.assertEqual(len(saved_df), 2)
        self.assertIn('Number', saved_df.columns)
        self.assertIn('Lookup_Status', saved_df.columns)
        self.assertNotIn('Cleaned_Number', saved_df.columns)  # Should be removed
    
    def test_get_processing_stats(self):
        """Test getting processing statistics."""
        self.phone_lookup.processed_count = 10
        self.phone_lookup.error_count = 2
        self.phone_lookup.is_running = True
        
        stats = self.phone_lookup.get_processing_stats()
        
        self.assertEqual(stats['processed_count'], 10)
        self.assertEqual(stats['error_count'], 2)
        self.assertTrue(stats['is_running'])
        self.assertIn('api_usage', stats)
    
    def test_stop_method(self):
        """Test stopping the phone lookup process."""
        self.phone_lookup.is_running = True
        self.phone_lookup.stop()
        
        self.assertFalse(self.phone_lookup.is_running)


class TestPhoneLookupIntegration(unittest.TestCase):
    """Integration tests for PhoneLookup."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.phone_lookup = PhoneLookup()
        self.test_input_file = Path(tempfile.mktemp(suffix=".xlsx"))
        self.test_output_file = Path(tempfile.mktemp(suffix=".xlsx"))
        
        # Create test data
        test_data = {
            'Number': ['923001234567', '923001234568']
        }
        df = pd.DataFrame(test_data)
        df.to_excel(self.test_input_file, index=False)
    
    def tearDown(self):
        """Clean up integration test files."""
        for file_path in [self.test_input_file, self.test_output_file]:
            if file_path.exists():
                file_path.unlink()
    
    @patch('modules.phone_lookup.requests.Session')
    def test_complete_processing_flow(self, mock_session):
        """Test complete processing flow with mocked API."""
        # Mock API responses
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "fullName": "Test User",
                "otherNames": ["Test"],
                "image": "http://example.com/test.jpg"
            }
        }
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Configure callbacks
        mock_log = Mock()
        mock_status = Mock()
        mock_progress = Mock()
        mock_usage = Mock()
        mock_stop = Mock(return_value=False)
        
        self.phone_lookup.configure(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file),
            api_key='test_key',
            delay=0.1,  # Short delay for testing
            log_callback=mock_log,
            status_callback=mock_status,
            progress_callback=mock_progress,
            usage_callback=mock_usage,
            stop_callback=mock_stop
        )
        
        # Run processing
        success = self.phone_lookup.run()
        
        # Verify results
        self.assertTrue(success)
        self.assertTrue(self.test_output_file.exists())
        
        # Verify callbacks were called
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_status.called)
        self.assertTrue(mock_progress.called)
        self.assertTrue(mock_usage.called)
        
        # Verify output file
        output_df = pd.read_excel(self.test_output_file)
        self.assertEqual(len(output_df), 2)
        self.assertIn('Full_Name', output_df.columns)
        self.assertIn('Image_URLs', output_df.columns)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_validate_phone_number(self):
        """Test phone number validation."""
        test_cases = [
            ('923001234567', True, "Valid"),      # Valid
            ('03001234567', True, "Valid"),       # Valid with 0
            ('12345', False, "Phone number too short"),  # Too short
            ('abc123', False, "Phone number too short"), # Contains letters
            ('', False, "Empty phone number"),    # Empty
            (None, False, "Empty phone number"),  # None
        ]
        
        for number, expected_valid, expected_message in test_cases:
            with self.subTest(number=number):
                is_valid, message = validate_phone_number(number)
                self.assertEqual(is_valid, expected_valid)
                self.assertIn(expected_message, message)
    
    @patch('modules.phone_lookup.PhoneLookup._lookup_phone_number')
    def test_batch_lookup_numbers(self, mock_lookup):
        """Test batch lookup function."""
        # Mock individual lookups
        mock_lookup.side_effect = [
            {
                "status": "Success",
                "full_name": "User One",
                "other_names": [],
                "image_urls": [],
                "base64_images": [],
                "error_message": ""
            },
            {
                "status": "Error",
                "full_name": "",
                "other_names": [],
                "image_urls": [],
                "base64_images": [],
                "error_message": "API error"
            }
        ]
        
        numbers = ['923001234567', '923001234568']
        results = batch_lookup_numbers(numbers, 'test_key', delay=0)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['status'], 'Success')
        self.assertEqual(results[1]['status'], 'Error')
        self.assertEqual(mock_lookup.call_count, 2)


class TestErrorScenarios(unittest.TestCase):
    """Test error scenarios and edge cases."""
    
    def test_invalid_input_file(self):
        """Test handling of invalid input file."""
        phone_lookup = PhoneLookup()
        
        phone_lookup.configure(
            input_file='nonexistent_file.xlsx',
            output_file='output.xlsx',
            api_key='test_key'
        )
        
        success = phone_lookup.run()
        self.assertFalse(success)
    
    def test_missing_number_column(self):
        """Test handling of missing Number column."""
        phone_lookup = PhoneLookup()
        
        # Create test file without Number column
        test_file = Path(tempfile.mktemp(suffix=".xlsx"))
        test_data = {'Name': ['User1', 'User2']}  # No Number column
        df = pd.DataFrame(test_data)
        df.to_excel(test_file, index=False)
        
        phone_lookup.configure(
            input_file=str(test_file),
            output_file='output.xlsx',
            api_key='test_key'
        )
        
        success = phone_lookup.run()
        self.assertFalse(success)
        
        # Clean up
        if test_file.exists():
            test_file.unlink()
    
    def test_empty_dataframe(self):
        """Test handling of empty input dataframe."""
        phone_lookup = PhoneLookup()
        
        # Create empty test file
        test_file = Path(tempfile.mktemp(suffix=".xlsx"))
        df = pd.DataFrame(columns=['Number'])
        df.to_excel(test_file, index=False)
        
        phone_lookup.configure(
            input_file=str(test_file),
            output_file='output.xlsx',
            api_key='test_key'
        )
        
        # This should complete successfully but process 0 numbers
        success = phone_lookup.run()
        self.assertTrue(success)  # Should complete without errors
        
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == '__main__':
    # Create test data directory
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)