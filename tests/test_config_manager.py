# tests/test_config_manager.py
import unittest
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock
import json
import base64

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from modules.config_manager import ConfigManager, create_default_config, get_config_manager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config_file = Path(tempfile.mktemp(suffix=".json"))
        self.config_manager = ConfigManager(str(self.test_config_file))
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test config file if it exists
        if self.test_config_file.exists():
            self.test_config_file.unlink()
        
        # Remove encryption key file if it exists
        key_file = self.test_config_file.parent / ".encryption_key"
        if key_file.exists():
            key_file.unlink()
    
    def test_initialization(self):
        """Test that ConfigManager initializes correctly."""
        self.assertIsInstance(self.config_manager, ConfigManager)
        self.assertEqual(self.config_manager.config_file, self.test_config_file)
        self.assertIsNotNone(self.config_manager.encryption_key)
        self.assertIsInstance(self.config_manager.config, dict)
    
    def test_initialization_with_nonexistent_file(self):
        """Test initialization with non-existent config file."""
        # Should create default config when file doesn't exist
        self.assertIsInstance(self.config_manager.config, dict)
        self.assertIn('api_key', self.config_manager.config)
        self.assertIn('request_delay', self.config_manager.config)
    
    def test_get_default_config(self):
        """Test default configuration structure."""
        default_config = self.config_manager._get_default_config()
        
        # Check required keys exist
        required_keys = [
            'api_key', 'api_host', 'request_delay', 'save_interval',
            'max_image_width', 'max_image_height', 'auto_save_config'
        ]
        for key in required_keys:
            self.assertIn(key, default_config)
        
        # Check default values
        self.assertEqual(default_config['api_key'], '')
        self.assertEqual(default_config['api_host'], 'eyecon.p.rapidapi.com')
        self.assertEqual(default_config['request_delay'], 1.5)
        self.assertEqual(default_config['max_image_width'], 100)
    
    def test_encryption_key_creation(self):
        """Test encryption key creation and loading."""
        # Key should be created during initialization
        key_file = self.test_config_file.parent / ".encryption_key"
        self.assertTrue(key_file.exists())
        
        # Key should be valid Fernet key
        from cryptography.fernet import Fernet
        try:
            Fernet(self.config_manager.encryption_key)
        except Exception:
            self.fail("Encryption key is not valid")
    
    def test_encryption_key_reuse(self):
        """Test that existing encryption key is reused."""
        # Get the original key
        original_key = self.config_manager.encryption_key
        
        # Create new config manager - should reuse same key
        new_manager = ConfigManager(str(self.test_config_file))
        
        self.assertEqual(original_key, new_manager.encryption_key)
    
    def test_encryption_and_decryption(self):
        """Test encryption and decryption of sensitive data."""
        test_data = "super_secret_api_key_12345"
        
        # Encrypt the data
        encrypted = self.config_manager._encrypt_value(test_data)
        
        # Should not be the same as original
        self.assertNotEqual(encrypted, test_data)
        
        # Decrypt should return original
        decrypted = self.config_manager._decrypt_value(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_encryption_empty_value(self):
        """Test encryption with empty values."""
        encrypted = self.config_manager._encrypt_value('')
        self.assertEqual(encrypted, '')
        
        encrypted = self.config_manager._encrypt_value(None)
        self.assertEqual(encrypted, None)
    
    def test_decryption_empty_value(self):
        """Test decryption with empty values."""
        decrypted = self.config_manager._decrypt_value('')
        self.assertEqual(decrypted, '')
        
        decrypted = self.config_manager._decrypt_value(None)
        self.assertEqual(decrypted, None)
    
    def test_decryption_invalid_data(self):
        """Test decryption with invalid encrypted data."""
        # Should return the input as-is if decryption fails
        invalid_encrypted = "not_properly_encrypted_data"
        result = self.config_manager._decrypt_value(invalid_encrypted)
        self.assertEqual(result, invalid_encrypted)
    
    def test_save_config(self):
        """Test saving configuration to file."""
        # Modify some values
        self.config_manager.set('api_key', 'test_key_123', auto_save=False)
        self.config_manager.set('request_delay', 2.0, auto_save=False)
        
        # Save configuration
        success = self.config_manager.save_config()
        
        self.assertTrue(success)
        self.assertTrue(self.test_config_file.exists())
        
        # Verify file content
        with open(self.test_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertIn('api_key', saved_data)
        self.assertIn('request_delay', saved_data)
        self.assertEqual(saved_data['request_delay'], 2.0)
        # API key should be encrypted in saved file
        self.assertNotEqual(saved_data['api_key'], 'test_key_123')
    
    def test_save_config_creates_directory(self):
        """Test that save_config creates directory if needed."""
        # Use a path in a non-existent directory
        deep_config_file = self.test_config_file.parent / "deep" / "dir" / "config.json"
        deep_manager = ConfigManager(str(deep_config_file))
        
        success = deep_manager.save_config()
        
        self.assertTrue(success)
        self.assertTrue(deep_config_file.exists())
        
        # Clean up
        if deep_config_file.exists():
            deep_config_file.unlink()
        if deep_config_file.parent.exists():
            deep_config_file.parent.rmdir()
        if deep_config_file.parent.parent.exists():
            deep_config_file.parent.parent.rmdir()
    
    def test_load_config(self):
        """Test loading configuration from file."""
        # Create a test config file
        test_config = {
            'api_key': 'original_key',
            'request_delay': 3.0,
            'max_image_width': 150
        }
        
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # Create new manager that should load this file
        new_manager = ConfigManager(str(self.test_config_file))
        
        self.assertEqual(new_manager.get('request_delay'), 3.0)
        self.assertEqual(new_manager.get('max_image_width'), 150)
    
    def test_load_config_corrupted_file(self):
        """Test loading corrupted config file."""
        # Create corrupted JSON file
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            f.write('invalid json content {')
        
        # Should fall back to default config
        new_manager = ConfigManager(str(self.test_config_file))
        
        # Should have default values
        self.assertEqual(new_manager.get('api_key'), '')
        self.assertEqual(new_manager.get('request_delay'), 1.5)
    
    def test_get_and_set_methods(self):
        """Test get and set methods."""
        # Test setting values
        self.config_manager.set('api_key', 'new_test_key')
        self.config_manager.set('request_delay', 2.5)
        self.config_manager.set('custom_setting', 'custom_value')
        
        # Test getting values
        self.assertEqual(self.config_manager.get('api_key'), 'new_test_key')
        self.assertEqual(self.config_manager.get('request_delay'), 2.5)
        self.assertEqual(self.config_manager.get('custom_setting'), 'custom_value')
        
        # Test default values
        self.assertEqual(self.config_manager.get('non_existent_key'), None)
        self.assertEqual(self.config_manager.get('non_existent_key', 'default'), 'default')
    
    def test_get_api_key(self):
        """Test secure API key retrieval."""
        # Set API key
        test_key = 'secure_api_key_12345'
        self.config_manager.set_api_key(test_key)
        
        # Retrieve using secure method
        retrieved_key = self.config_manager.get_api_key()
        
        self.assertEqual(retrieved_key, test_key)
    
    def test_set_api_key(self):
        """Test secure API key setting."""
        test_key = 'another_secure_key_67890'
        
        success = self.config_manager.set_api_key(test_key)
        
        self.assertTrue(success)
        self.assertEqual(self.config_manager.get_api_key(), test_key)
    
    def test_auto_save_config(self):
        """Test automatic saving when auto_save_config is enabled."""
        # Enable auto-save (default)
        self.config_manager.set('auto_save_config', True)
        
        # Modify a value - should trigger auto-save
        self.config_manager.set('request_delay', 3.0)
        
        # Verify file was saved
        self.assertTrue(self.test_config_file.exists())
        
        # Load and verify the change was saved
        with open(self.test_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['request_delay'], 3.0)
    
    def test_auto_save_config_disabled(self):
        """Test that auto-save can be disabled."""
        # Disable auto-save
        self.config_manager.set('auto_save_config', False, auto_save=False)
        
        # Modify a value - should not trigger auto-save
        self.config_manager.set('request_delay', 4.0, auto_save=False)
        
        # File should not exist yet (unless created by previous tests)
        if not self.test_config_file.exists():
            # Manual save should work
            success = self.config_manager.save_config()
            self.assertTrue(success)
    
    def test_validate_config(self):
        """Test configuration validation."""
        # Test valid configuration
        self.config_manager.set_api_key('valid_key_1234567890')
        self.config_manager.set('request_delay', 1.5)
        self.config_manager.set('save_interval', 10)
        self.config_manager.set('max_requests_per_minute', 60)
        self.config_manager.set('max_image_width', 100)
        self.config_manager.set('max_image_height', 100)
        
        errors = self.config_manager.validate_config()
        self.assertEqual(len(errors), 0)
    
    def test_validate_config_missing_api_key(self):
        """Test validation with missing API key."""
        self.config_manager.set_api_key('')  # Empty API key
        
        errors = self.config_manager.validate_config()
        self.assertIn("API key is required", errors)
    
    def test_validate_config_short_api_key(self):
        """Test validation with short API key."""
        self.config_manager.set_api_key('short')  # Too short
        
        errors = self.config_manager.validate_config()
        self.assertIn("API key appears to be invalid", errors)
    
    def test_validate_config_invalid_delay(self):
        """Test validation with invalid request delay."""
        self.config_manager.set('request_delay', 0.05)  # Too small
        
        errors = self.config_manager.validate_config()
        self.assertIn("Request delay must be between 0.1 and 10 seconds", errors)
        
        self.config_manager.set('request_delay', 15.0)  # Too large
        errors = self.config_manager.validate_config()
        self.assertIn("Request delay must be between 0.1 and 10 seconds", errors)
    
    def test_validate_config_invalid_image_dimensions(self):
        """Test validation with invalid image dimensions."""
        self.config_manager.set('max_image_width', 5)  # Too small
        
        errors = self.config_manager.validate_config()
        self.assertIn("Max image width must be between 10 and 1000 pixels", errors)
        
        self.config_manager.set('max_image_width', 2000)  # Too large
        errors = self.config_manager.validate_config()
        self.assertIn("Max image width must be between 10 and 1000 pixels", errors)
        
        self.config_manager.set('max_image_height', 5)  # Too small
        errors = self.config_manager.validate_config()
        self.assertIn("Max image height must be between 10 and 1000 pixels", errors)
    
    def test_is_api_configured(self):
        """Test API configuration check."""
        # Initially not configured
        self.assertFalse(self.config_manager.is_api_configured())
        
        # Configure with valid key
        self.config_manager.set_api_key('valid_key_1234567890')
        self.assertTrue(self.config_manager.is_api_configured())
        
        # Configure with invalid key
        self.config_manager.set_api_key('short')
        self.assertFalse(self.config_manager.is_api_configured())
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        # Modify some values
        self.config_manager.set('api_key', 'test_key')
        self.config_manager.set('request_delay', 5.0)
        self.config_manager.set('custom_setting', 'value')
        
        # Reset to defaults
        success = self.config_manager.reset_to_defaults()
        
        self.assertTrue(success)
        
        # Check values are reset to defaults
        self.assertEqual(self.config_manager.get('api_key'), '')
        self.assertEqual(self.config_manager.get('request_delay'), 1.5)
        self.assertNotIn('custom_setting', self.config_manager.config)
    
    def test_get_config_summary(self):
        """Test getting safe configuration summary."""
        # Set some values including sensitive ones
        self.config_manager.set_api_key('super_secret_key_12345')
        self.config_manager.set('request_delay', 2.0)
        self.config_manager.set('proxy_password', 'secret_proxy_pass')
        self.config_manager.set('webhook_secret', 'webhook_secret_123')
        
        summary = self.config_manager.get_config_summary()
        
        # Sensitive fields should be masked
        self.assertNotEqual(summary['api_key'], 'super_secret_key_12345')
        self.assertTrue(summary['api_key'].startswith('***'))
        
        self.assertNotEqual(summary['proxy_password'], 'secret_proxy_pass')
        self.assertTrue(summary['proxy_password'].startswith('***'))
        
        # Non-sensitive fields should be unchanged
        self.assertEqual(summary['request_delay'], 2.0)
    
    def test_export_config(self):
        """Test exporting configuration."""
        export_file = Path(tempfile.mktemp(suffix=".json"))
        
        # Set some values
        self.config_manager.set('request_delay', 2.5)
        self.config_manager.set('max_image_width', 150)
        
        success = self.config_manager.export_config(export_file)
        
        self.assertTrue(success)
        self.assertTrue(export_file.exists())
        
        # Verify exported content
        with open(export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        self.assertEqual(exported_data['request_delay'], 2.5)
        self.assertEqual(exported_data['max_image_width'], 150)
        # Sensitive data should be masked
        self.assertTrue(exported_data['api_key'].startswith('***'))
        
        # Clean up
        if export_file.exists():
            export_file.unlink()
    
    def test_import_config(self):
        """Test importing configuration."""
        # Create export file first
        export_file = Path(tempfile.mktemp(suffix=".json"))
        export_data = {
            'request_delay': 3.0,
            'max_image_width': 200,
            'max_image_height': 200,
            'api_key': '***1234'  # Masked in export
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f)
        
        # Import configuration
        success = self.config_manager.import_config(export_file)
        
        self.assertTrue(success)
        
        # Check values were imported
        self.assertEqual(self.config_manager.get('request_delay'), 3.0)
        self.assertEqual(self.config_manager.get('max_image_width'), 200)
        self.assertEqual(self.config_manager.get('max_image_height'), 200)
        # Masked API key should not be imported
        self.assertNotEqual(self.config_manager.get('api_key'), '***1234')
        
        # Clean up
        if export_file.exists():
            export_file.unlink()
    
    def test_import_config_invalid_file(self):
        """Test importing invalid configuration file."""
        invalid_file = Path(tempfile.mktemp(suffix=".json"))
        
        # Create file with invalid data
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write('invalid json {')
        
        success = self.config_manager.import_config(invalid_file)
        
        self.assertFalse(success)
        
        # Clean up
        if invalid_file.exists():
            invalid_file.unlink()
    
    def test_import_config_invalid_structure(self):
        """Test importing configuration with invalid structure."""
        invalid_file = Path(tempfile.mktemp(suffix=".json"))
        
        # Create file with missing required structure
        invalid_data = {'some_random_key': 'value'}
        
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        success = self.config_manager.import_config(invalid_file)
        
        self.assertFalse(success)
        
        # Clean up
        if invalid_file.exists():
            invalid_file.unlink()
    
    def test_string_representation(self):
        """Test string representation methods."""
        str_repr = str(self.config_manager)
        self.assertIn('ConfigManager', str_repr)
        self.assertIn('api_configured', str_repr)
        
        repr_str = repr(self.config_manager)
        self.assertIn('ConfigManager', repr_str)
        self.assertIn(str(self.test_config_file), repr_str)


class TestConfigManagerEncryption(unittest.TestCase):
    """Test encryption-related functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config_file = Path(tempfile.mktemp(suffix=".json"))
    
    def tearDown(self):
        """Clean up after tests."""
        if self.test_config_file.exists():
            self.test_config_file.unlink()
        
        key_file = self.test_config_file.parent / ".encryption_key"
        if key_file.exists():
            key_file.unlink()
    
    def test_encryption_persistence(self):
        """Test that encryption persists across instances."""
        # Create first manager and set encrypted value
        manager1 = ConfigManager(str(self.test_config_file))
        secret_value = "very_secret_data"
        manager1.set('api_key', secret_value)
        manager1.save_config()
        
        # Create second manager - should decrypt correctly
        manager2 = ConfigManager(str(self.test_config_file))
        decrypted_value = manager2.get_api_key()
        
        self.assertEqual(decrypted_value, secret_value)
    
    def test_multiple_sensitive_fields(self):
        """Test encryption of multiple sensitive fields."""
        manager = ConfigManager(str(self.test_config_file))
        
        sensitive_data = {
            'api_key': 'api_secret_123',
            'proxy_password': 'proxy_secret_456',
            'webhook_secret': 'webhook_secret_789'
        }
        
        for key, value in sensitive_data.items():
            manager.set(key, value)
        
        manager.save_config()
        
        # Verify saved file has encrypted values
        with open(self.test_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        for key in sensitive_data.keys():
            self.assertIn(key, saved_data)
            self.assertNotEqual(saved_data[key], sensitive_data[key])
        
        # Verify decryption works
        new_manager = ConfigManager(str(self.test_config_file))
        for key, expected_value in sensitive_data.items():
            self.assertEqual(new_manager.get(key), expected_value)
    
    @patch('modules.config_manager.open')
    def test_encryption_key_file_error(self, mock_open):
        """Test behavior when encryption key file cannot be created."""
        mock_open.side_effect = IOError("Permission denied")
        
        # Should use fallback key
        manager = ConfigManager(str(self.test_config_file))
        
        self.assertIsNotNone(manager.encryption_key)
        # Should still be able to encrypt/decrypt
        test_data = "test_data"
        encrypted = manager._encrypt_value(test_data)
        decrypted = manager._decrypt_value(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_fallback_encryption_key(self):
        """Test fallback encryption key generation."""
        # Mock the file operations to force fallback
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.unlink') as mock_unlink, \
             patch('builtins.open') as mock_open:
            
            mock_exists.return_value = False
            mock_open.side_effect = IOError("Cannot create key file")
            
            manager = ConfigManager(str(self.test_config_file))
            
            # Should have a fallback key
            self.assertIsNotNone(manager.encryption_key)
            
            # Encryption/decryption should still work
            test_data = "fallback_test_data"
            encrypted = manager._encrypt_value(test_data)
            decrypted = manager._decrypt_value(encrypted)
            self.assertEqual(decrypted, test_data)


class TestConfigManagerConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config_file = Path(tempfile.mktemp(suffix=".json"))
    
    def tearDown(self):
        """Clean up after tests."""
        if self.test_config_file.exists():
            self.test_config_file.unlink()
        
        key_file = self.test_config_file.parent / ".encryption_key"
        if key_file.exists():
            key_file.unlink()
    
    def test_create_default_config(self):
        """Test create_default_config function."""
        success = create_default_config(str(self.test_config_file))
        
        self.assertTrue(success)
        self.assertTrue(self.test_config_file.exists())
        
        # Verify file has default structure
        with open(self.test_config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        self.assertIn('api_key', config_data)
        self.assertIn('request_delay', config_data)
    
    def test_get_config_manager_singleton(self):
        """Test get_config_manager singleton pattern."""
        manager1 = get_config_manager(str(self.test_config_file))
        manager2 = get_config_manager(str(self.test_config_file))
        
        # Should return the same instance
        self.assertIs(manager1, manager2)
    
    def test_get_config_manager_different_files(self):
        """Test get_config_manager with different files."""
        file1 = Path(tempfile.mktemp(suffix=".json"))
        file2 = Path(tempfile.mktemp(suffix=".json"))
        
        try:
            manager1 = get_config_manager(str(file1))
            manager2 = get_config_manager(str(file2))
            
            # Should be different instances for different files
            self.assertIsNot(manager1, manager2)
        finally:
            # Clean up
            for f in [file1, file2]:
                if f.exists():
                    f.unlink()
                key_file = f.parent / ".encryption_key"
                if key_file.exists():
                    key_file.unlink()


class TestConfigManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_save_config_permission_error(self):
        """Test saving config with permission error."""
        manager = ConfigManager(str(Path('/readonly/config.json')))
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = PermissionError("Read-only file system")
            
            success = manager.save_config()
            
            self.assertFalse(success)
    
    def test_load_config_permission_error(self):
        """Test loading config with permission error."""
        test_file = Path(tempfile.mktemp(suffix=".json"))
        test_file.touch()
        test_file.chmod(0o000)  # No permissions
        
        try:
            manager = ConfigManager(str(test_file))
            # Should fall back to default config
            self.assertEqual(manager.get('api_key'), '')
        finally:
            # Restore permissions to allow cleanup
            test_file.chmod(0o644)
            if test_file.exists():
                test_file.unlink()
    
    def test_config_with_special_characters(self):
        """Test configuration with special characters."""
        manager = ConfigManager(str(Path(tempfile.mktemp(suffix=".json"))))
        
        special_values = {
            'api_key': 'key_with_!@#$%^&*()_+',
            'proxy_url': 'http://user:pass@host:port/path?query=value',
            'webhook_url': 'https://api.example.com/v1/webhook?token=abc123'
        }
        
        for key, value in special_values.items():
            manager.set(key, value)
        
        manager.save_config()
        
        # Verify values are preserved
        for key, expected_value in special_values.items():
            self.assertEqual(manager.get(key), expected_value)
    
    def test_large_configuration(self):
        """Test configuration with many settings."""
        manager = ConfigManager(str(Path(tempfile.mktemp(suffix=".json"))))
        
        # Add many settings
        for i in range(100):
            manager.set(f'custom_setting_{i}', f'value_{i}')
        
        success = manager.save_config()
        
        self.assertTrue(success)
        
        # Verify all settings are preserved
        for i in range(100):
            self.assertEqual(manager.get(f'custom_setting_{i}'), f'value_{i}')


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)