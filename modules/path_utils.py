# modules/path_utils.py
import os
import sys
from pathlib import Path
from typing import Optional


def get_app_base_path() -> Path:
    """
    Get the appropriate base path for storing data files.
    Works in both development and packaged environments.
    
    Returns:
        Path: Base directory path for application data
    """
    if is_compiled():
        # Running as compiled executable
        if sys.platform == "win32":
            # Windows: Use AppData/Local
            base_path = Path(os.environ.get('LOCALAPPDATA', Path.home())) / "PhoneLookupTool"
        elif sys.platform == "darwin":
            # macOS: Use ~/Library/Application Support
            base_path = Path.home() / "Library" / "Application Support" / "PhoneLookupTool"
        else:
            # Linux: Use ~/.local/share
            base_path = Path.home() / ".local" / "share" / "PhoneLookupTool"
    else:
        # Running as script - use project root
        base_path = Path(__file__).parent.parent
    
    # Create directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def get_data_path() -> Path:
    """
    Get path for data storage (usage data, cache, etc.).
    
    Returns:
        Path: Data directory path
    """
    data_path = get_app_base_path() / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def get_logs_path() -> Path:
    """
    Get path for log files.
    
    Returns:
        Path: Logs directory path
    """
    logs_path = get_app_base_path() / "logs"
    logs_path.mkdir(parents=True, exist_ok=True)
    return logs_path


def get_config_path() -> Path:
    """
    Get path for configuration files.
    
    Returns:
        Path: Config directory path
    """
    config_path = get_app_base_path() / "config"
    config_path.mkdir(parents=True, exist_ok=True)
    return config_path


def get_cache_path() -> Path:
    """
    Get path for cached files (images, temporary data).
    
    Returns:
        Path: Cache directory path
    """
    cache_path = get_app_base_path() / "cache"
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def get_temp_path() -> Path:
    """
    Get path for temporary files.
    
    Returns:
        Path: Temp directory path
    """
    temp_path = get_app_base_path() / "temp"
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


def get_backup_path() -> Path:
    """
    Get path for backup files.
    
    Returns:
        Path: Backup directory path
    """
    backup_path = get_app_base_path() / "backups"
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def is_compiled() -> bool:
    """
    Check if running as compiled executable.
    
    Returns:
        bool: True if running as compiled executable, False if running as script
    """
    return getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Use for assets that are included in the package.
    
    Args:
        relative_path: Relative path to resource
        
    Returns:
        Path: Absolute path to resource
    """
    if is_compiled():
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(sys.executable).parent
    else:
        # Running as script
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


def get_default_input_path() -> Path:
    """
    Get default path for input files (user's Desktop or Documents).
    
    Returns:
        Path: Default input directory path
    """
    # Try Desktop first, then Documents
    desktop = Path.home() / "Desktop"
    documents = Path.home() / "Documents"
    
    if desktop.exists():
        return desktop
    elif documents.exists():
        return documents
    else:
        return Path.home()


def get_default_output_path() -> Path:
    """
    Get default path for output files (user's Desktop or Documents).
    
    Returns:
        Path: Default output directory path
    """
    return get_default_input_path()  # Same as input for convenience


def ensure_directory(path: Path) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path to ensure
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_file_size(file_path: Path) -> Optional[int]:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        Optional[int]: File size in bytes, or None if file doesn't exist
    """
    try:
        return file_path.stat().st_size
    except (OSError, AttributeError):
        return None


def get_file_age_days(file_path: Path) -> Optional[float]:
    """
    Get file age in days.
    
    Args:
        file_path: Path to file
        
    Returns:
        Optional[float]: File age in days, or None if file doesn't exist
    """
    try:
        import time
        from datetime import datetime
        
        file_mtime = file_path.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - file_mtime
        age_days = age_seconds / (24 * 3600)
        
        return age_days
    except (OSError, AttributeError):
        return None


def cleanup_old_files(directory: Path, pattern: str = "*", max_age_days: int = 30) -> int:
    """
    Clean up old files in a directory.
    
    Args:
        directory: Directory to clean up
        pattern: File pattern to match (e.g., "*.log")
        max_age_days: Maximum file age in days
        
    Returns:
        int: Number of files deleted
    """
    if not directory.exists():
        return 0
    
    deleted_count = 0
    current_time = os.path.getmtime.__code__.co_filename  # Just to have a reference
    
    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_age = get_file_age_days(file_path)
                if file_age and file_age > max_age_days:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        pass  # Skip files that can't be deleted
    except Exception:
        pass  # Skip if cleanup fails
    
    return deleted_count


def get_available_space(path: Path) -> Optional[int]:
    """
    Get available disk space in bytes for the path's filesystem.
    
    Args:
        path: Path to check disk space for
        
    Returns:
        Optional[int]: Available space in bytes, or None if unable to determine
    """
    try:
        if hasattr(os, 'statvfs'):  # Unix-like systems
            stat = os.statvfs(path)
            return stat.f_bavail * stat.f_frsize
        else:  # Windows
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(str(path)), 
                None, None, 
                ctypes.pointer(free_bytes)
            )
            return free_bytes.value
    except Exception:
        return None


def is_path_writable(path: Path) -> bool:
    """
    Check if a path is writable.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if path is writable
    """
    try:
        # Try to create a test file
        test_file = path / ".write_test"
        test_file.touch()
        test_file.unlink()  # Clean up
        return True
    except (OSError, IOError):
        return False


def get_relative_path(from_path: Path, to_path: Path) -> Path:
    """
    Get relative path from one path to another.
    
    Args:
        from_path: Starting path
        to_path: Target path
        
    Returns:
        Path: Relative path from from_path to to_path
    """
    try:
        return to_path.relative_to(from_path)
    except ValueError:
        # Paths are not relative, return absolute path
        return to_path


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Convert a string to a safe filename.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        str: Safe filename
    """
    # Replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Truncate if too long
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:max_length - len(ext)] + ext
    
    # Ensure not empty
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name


def get_directory_size(directory: Path) -> int:
    """
    Calculate total size of all files in a directory (recursive).
    
    Args:
        directory: Directory to calculate size for
        
    Returns:
        int: Total size in bytes
    """
    total_size = 0
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except (OSError, PermissionError):
        pass  # Skip files we can't access
    
    return total_size


# Initialize required directories on import
def initialize_app_directories() -> bool:
    """
    Initialize all required application directories.
    
    Returns:
        bool: True if all directories were created successfully
    """
    directories = [
        get_app_base_path(),
        get_data_path(),
        get_logs_path(),
        get_config_path(),
        get_cache_path(),
        get_temp_path(),
        get_backup_path()
    ]
    
    success = True
    for directory in directories:
        if not ensure_directory(directory):
            success = False
    
    return success


# Platform-specific utilities
def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith("linux")


def get_platform_name() -> str:
    """Get human-readable platform name."""
    if is_windows():
        return "Windows"
    elif is_macos():
        return "macOS"
    elif is_linux():
        return "Linux"
    else:
        return sys.platform


# Import regex for safe_filename
import re

# Initialize directories when module is imported
initialize_app_directories()


# Test function
def _test_path_utils():
    """Test all path utility functions."""
    print("Testing path_utils...")
    
    # Test basic paths
    base_path = get_app_base_path()
    data_path = get_data_path()
    logs_path = get_logs_path()
    config_path = get_config_path()
    
    print(f"Base path: {base_path}")
    print(f"Data path: {data_path}")
    print(f"Logs path: {logs_path}")
    print(f"Config path: {config_path}")
    
    # Test platform detection
    print(f"Platform: {get_platform_name()}")
    print(f"Compiled: {is_compiled()}")
    
    # Test directory creation
    print(f"Directories initialized: {initialize_app_directories()}")
    
    # Test file operations
    test_file = data_path / "test.txt"
    try:
        test_file.write_text("test")
        file_size = get_file_size(test_file)
        print(f"File size: {file_size} bytes")
        test_file.unlink()
    except Exception as e:
        print(f"File test failed: {e}")
    
    # Test safe filename
    unsafe_name = 'file<>:"/\\|?*name.txt'
    safe_name = safe_filename(unsafe_name)
    print(f"Safe filename: '{unsafe_name}' -> '{safe_name}'")
    
    print("Path utils test completed!")


if __name__ == "__main__":
    _test_path_utils()