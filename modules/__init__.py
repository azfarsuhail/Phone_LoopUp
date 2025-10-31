"""
Phone Lookup Tool Modules
"""

__version__ = "1.0.0"
__author__ = "Azfar Suhail"
__description__ = "Core modules for Phone Lookup Tool application"

# Import key classes for easier access
from .phone_lookup import PhoneLookup
from .image_embedder import ImageEmbedder
from .usage_tracker import UsageTracker
from .path_utils import (
    get_app_base_path,
    get_data_path,
    get_logs_path,
    get_config_path,
    get_cache_path,
    get_temp_path,
    is_compiled,
    get_resource_path
)
from .config_manager import ConfigManager

# Define what gets imported with "from modules import *"
__all__ = [
    'PhoneLookup',
    'ImageEmbedder', 
    'UsageTracker',
    'ConfigManager',
    'get_app_base_path',
    'get_data_path', 
    'get_logs_path',
    'get_config_path',
    'get_cache_path',
    'get_temp_path',
    'is_compiled',
    'get_resource_path'
]

# Package initialization
print(f"Initializing PhoneLookupTool modules v{__version__}")