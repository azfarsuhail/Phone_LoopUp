# modules/config_manager.py
import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from typing import Dict, Any, Optional, List

from .path_utils import get_config_path


class ConfigManager:
    """
    Secure configuration manager for Phone Lookup Tool.
    Handles API keys and application settings with encryption.
    """
    
    def __init__(self, config_file: str = "app_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Name of the configuration file
        """
        self.config_file = get_config_path() / config_file
        self.encryption_key = self._get_encryption_key()
        self.config = self._load_config()
    
    def _get_encryption_key(self) -> bytes:
        """
        Generate or retrieve encryption key for securing sensitive data.
        
        Returns:
            bytes: Encryption key
        """
        key_file = get_config_path() / ".encryption_key"
        
        if key_file.exists():
            # Load existing key
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                # Verify it's a valid Fernet key
                Fernet(key)
                return key
            except Exception as e:
                print(f"Warning: Invalid encryption key, generating new one: {e}")
                key_file.unlink()  # Remove invalid key file
        
        # Generate new key
        key = Fernet.generate_key()
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set file permissions and attributes
            if os.name == 'nt':
                # Windows: Set hidden attribute
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(key_file), 2)  # FILE_ATTRIBUTE_HIDDEN
            else:
                # Unix: Set restrictive permissions (read/write for owner only)
                key_file.chmod(0o600)
                
            return key
        except Exception as e:
            print(f"Error saving encryption key: {e}")
            # Return a deterministic key based on machine ID as fallback
            return self._get_fallback_key()
    
    def _get_fallback_key(self) -> bytes:
        """
        Generate a fallback encryption key based on machine-specific information.
        This is less secure but ensures the app works even if key file can't be created.
        """
        try:
            # Use a combination of machine-specific information
            import platform
            import socket
            
            machine_info = f"{platform.node()}-{socket.gethostname()}-PhoneLookupTool"
            salt = b"phone_lookup_tool_salt"
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_info.encode()))
            return key
        except Exception:
            # Ultimate fallback - fixed key (least secure)
            return base64.urlsafe_b64encode(b"phone-lookup-tool-fallback-key-32bytes!!")
    
    def _encrypt_value(self, value: str) -> str:
        """
        Encrypt a sensitive value.
        
        Args:
            value: Plaintext value to encrypt
            
        Returns:
            str: Encrypted value as string
        """
        if not value:
            return value
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted = fernet.encrypt(value.encode())
            return encrypted.decode('latin-1')  # Use latin-1 for reliable round-trip
        except Exception as e:
            print(f"Encryption error: {e}")
            return value  # Return plaintext as fallback
    
    def _decrypt_value(self, value: str) -> str:
        """
        Decrypt a sensitive value.
        
        Args:
            value: Encrypted value to decrypt
            
        Returns:
            str: Decrypted plaintext value
        """
        if not value:
            return value
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted = fernet.decrypt(value.encode('latin-1'))
            return decrypted.decode()
        except Exception:
            # If decryption fails, assume it's plaintext (for backward compatibility)
            return value
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict: Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Decrypt sensitive fields
                sensitive_fields = ['api_key', 'proxy_password', 'webhook_secret']
                for field in sensitive_fields:
                    if field in config and config[field]:
                        config[field] = self._decrypt_value(config[field])
                
                print(f"Configuration loaded from {self.config_file}")
                return config
            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f"Error loading config from {self.config_file}: {e}")
                print("Using default configuration")
                return self._get_default_config()
        else:
            print("No configuration file found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.
        
        Returns:
            Dict: Default configuration dictionary
        """
        return {
            # API Configuration
            "api_key": "",
            "api_host": "eyecon.p.rapidapi.com",
            "api_timeout": 30,
            
            # Processing Behavior
            "request_delay": 1.5,
            "save_interval": 10,
            "max_requests_per_minute": 60,
            "max_retries": 3,
            "retry_delay": 2.0,
            
            # Image Settings
            "max_image_width": 100,
            "max_image_height": 100,
            "image_quality": 85,
            "row_height": 75,
            "column_width": 15,
            
            # UI Settings
            "theme": "system",  # system, light, dark
            "auto_save_config": True,
            "show_notifications": True,
            "minimize_to_tray": False,
            
            # File Management
            "default_input_folder": str(Path.home() / "Desktop"),
            "default_output_folder": str(Path.home() / "Desktop"),
            "remember_last_folder": True,
            "auto_open_output": True,
            
            # Advanced Settings
            "enable_cache": True,
            "cache_duration_days": 7,
            "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
            "max_log_files": 5,
            "log_retention_days": 30,
            
            # Proxy Settings (optional)
            "use_proxy": False,
            "proxy_url": "",
            "proxy_username": "",
            "proxy_password": "",
            
            # Webhook/Integration (optional)
            "webhook_enabled": False,
            "webhook_url": "",
            "webhook_secret": "",
            
            # Version tracking
            "config_version": "1.0.0",
            "last_updated": None
        }
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update metadata
            self.config["last_updated"] = self._get_current_timestamp()
            self.config["config_version"] = "1.0.0"
            
            # Create a copy for saving (encrypt sensitive data)
            save_config = self.config.copy()
            sensitive_fields = ['api_key', 'proxy_password', 'webhook_secret']
            
            for field in sensitive_fields:
                if field in save_config and save_config[field]:
                    save_config[field] = self._encrypt_value(save_config[field])
            
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, indent=2, ensure_ascii=False)
            
            # Set appropriate file permissions
            if os.name == 'posix':  # Unix/Linux/macOS
                os.chmod(self.config_file, 0o600)  # Read/write for owner only
            
            print(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving config to {self.config_file}: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: ISO formatted timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = None) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            auto_save: Whether to save immediately (uses auto_save_config if None)
            
        Returns:
            bool: True if successful
        """
        self.config[key] = value
        
        # Determine if we should auto-save
        should_save = auto_save if auto_save is not None else self.get('auto_save_config', True)
        
        if should_save:
            return self.save_config()
        
        return True
    
    def get_api_key(self) -> str:
        """
        Safely get API key.
        
        Returns:
            str: API key
        """
        return self.get('api_key', '')
    
    def set_api_key(self, api_key: str, auto_save: bool = None) -> bool:
        """
        Safely set API key.
        
        Args:
            api_key: API key value
            auto_save: Whether to save immediately
            
        Returns:
            bool: True if successful
        """
        return self.set('api_key', api_key, auto_save)
    
    def validate_config(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        # API Key validation
        api_key = self.get_api_key()
        if not api_key:
            errors.append("API key is required")
        elif len(api_key) < 10:
            errors.append("API key appears to be invalid (too short)")
        
        # Numeric validations
        delay = self.get('request_delay', 1.5)
        if delay < 0.1 or delay > 10:
            errors.append("Request delay must be between 0.1 and 10 seconds")
        
        save_interval = self.get('save_interval', 10)
        if save_interval < 1 or save_interval > 1000:
            errors.append("Save interval must be between 1 and 1000")
        
        max_requests = self.get('max_requests_per_minute', 60)
        if max_requests < 1 or max_requests > 300:
            errors.append("Max requests per minute must be between 1 and 300")
        
        # Image dimension validations
        max_width = self.get('max_image_width', 100)
        if max_width < 10 or max_width > 1000:
            errors.append("Max image width must be between 10 and 1000 pixels")
        
        max_height = self.get('max_image_height', 100)
        if max_height < 10 or max_height > 1000:
            errors.append("Max image height must be between 10 and 1000 pixels")
        
        return errors
    
    def is_api_configured(self) -> bool:
        """
        Check if API is properly configured.
        
        Returns:
            bool: True if API key is present and appears valid
        """
        api_key = self.get_api_key()
        return bool(api_key and len(api_key) >= 10)
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.
        
        Returns:
            bool: True if successful
        """
        self.config = self._get_default_config()
        return self.save_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a safe summary of configuration (without sensitive data).
        
        Returns:
            Dict: Configuration summary
        """
        summary = self.config.copy()
        
        # Mask sensitive fields
        sensitive_fields = ['api_key', 'proxy_password', 'webhook_secret']
        for field in sensitive_fields:
            if field in summary and summary[field]:
                summary[field] = "***" + summary[field][-4:] if len(summary[field]) > 4 else "***"
        
        return summary
    
    def export_config(self, file_path: str) -> bool:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.get_config_summary(), f, indent=2, ensure_ascii=False)
            print(f"Configuration exported to {file_path}")
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported config has basic structure
            if not isinstance(imported_config, dict):
                print("Invalid config structure: not a dictionary")
                return False
            
            # Check if it has at least some expected keys
            expected_keys = ['api_host', 'request_delay', 'max_image_width']
            has_expected_keys = any(key in imported_config for key in expected_keys)
            
            if not has_expected_keys:
                print("Invalid config structure: missing expected configuration keys")
                return False
            
            # Update current config with imported values
            for key, value in imported_config.items():
                # Don't import sensitive fields from summary exports
                if not key.endswith('_key') and not key.endswith('_password') and not key.endswith('_secret'):
                    self.config[key] = value
            
            return self.save_config()
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation of configuration."""
        summary = self.get_config_summary()
        return f"ConfigManager(file='{self.config_file}', api_configured={self.is_api_configured()})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ConfigManager(file='{self.config_file}', api_configured={self.is_api_configured()})"


# Singleton cache
_config_manager_instances = {}

def create_default_config(config_file: str = "app_config.json") -> bool:
    """
    Create a default configuration file.
    
    Args:
        config_file: Configuration file name
        
    Returns:
        bool: True if successful
    """
    manager = ConfigManager(config_file)
    return manager.save_config()


def get_config_manager(config_file: str = "app_config.json") -> ConfigManager:
    """
    Get a ConfigManager instance (factory function with caching).
    
    Args:
        config_file: Configuration file name
        
    Returns:
        ConfigManager: ConfigManager instance
    """
    config_path = str(get_config_path() / config_file)
    
    if config_path not in _config_manager_instances:
        _config_manager_instances[config_path] = ConfigManager(config_file)
    
    return _config_manager_instances[config_path]


if __name__ == "__main__":
    # Test the configuration manager
    print("Testing ConfigManager...")
    
    manager = ConfigManager("test_config.json")
    
    # Test setting and getting values
    manager.set_api_key("test_api_key_12345")
    manager.set("request_delay", 2.0)
    
    print(f"API Key: {manager.get_api_key()}")
    print(f"Request Delay: {manager.get('request_delay')}")
    
    # Test validation
    errors = manager.validate_config()
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    # Test summary
    summary = manager.get_config_summary()
    print(f"Config summary: {summary}")
    
    # Clean up test file
    if manager.config_file.exists():
        manager.config_file.unlink()
    
    print("ConfigManager test completed!")