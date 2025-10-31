# modules/usage_tracker.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .path_utils import get_data_path


class UsageTracker:
    """
    API usage tracking and statistics manager.
    Tracks monthly API usage with persistent storage.
    """
    
    def __init__(self, storage_file: str = "api_usage.json"):
        """
        Initialize the usage tracker.
        
        Args:
            storage_file: Name of the JSON file for storing usage data
        """
        # Setup module-specific logger FIRST
        self.logger = self._setup_logger()
        
        # Then setup everything else
        self.storage_file = get_data_path() / storage_file
        self.current_month = datetime.now().strftime("%Y-%m")
        self.usage_data = self._load_usage_data()
        
        # Initialize current month if not exists
        self._ensure_current_month()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup module-specific logger."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            # Create logs directory if it doesn't exist
            log_dir = get_data_path() / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / "usage_tracker.log"
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_usage_data(self) -> Dict[str, Any]:
        """
        Load usage data from JSON file.
        
        Returns:
            Dict: Usage data dictionary
        """
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded usage data from {self.storage_file}")
                return data
            except (json.JSONDecodeError, KeyError, Exception) as e:
                self.logger.error(f"Error loading usage data: {e}")
                return self._get_default_usage_data()
        else:
            self.logger.info("No existing usage data found, starting fresh")
            return self._get_default_usage_data()
    
    def _get_default_usage_data(self) -> Dict[str, Any]:
        """
        Get default usage data structure.
        
        Returns:
            Dict: Default usage data structure
        """
        return {
            "metadata": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            "monthly_usage": {},
            "all_time_stats": {
                "total_requests": 0,
                "first_request": None,
                "last_request": None
            }
        }
    
    def _ensure_current_month(self) -> None:
        """Ensure current month exists in usage data."""
        if self.current_month not in self.usage_data["monthly_usage"]:
            self.usage_data["monthly_usage"][self.current_month] = {
                "count": 0,
                "first_request": datetime.now().isoformat(),
                "last_request": None,
                "daily_breakdown": {}
            }
            self._save_usage_data()
    
    def _save_usage_data(self) -> bool:
        """
        Save usage data to JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update metadata
            self.usage_data["metadata"]["last_updated"] = datetime.now().isoformat()
            self.usage_data["metadata"]["version"] = "1.0.0"
            
            # Ensure directory exists
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Usage data saved to {self.storage_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving usage data: {e}")
            return False
    
    def increment_usage(self, count: int = 1) -> bool:
        """
        Increment API usage counter for current month.
        
        Args:
            count: Number of requests to add
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if month has changed
            current_month = datetime.now().strftime("%Y-%m")
            if current_month != self.current_month:
                self.current_month = current_month
                self._ensure_current_month()
            
            # Update monthly usage
            self.usage_data["monthly_usage"][self.current_month]["count"] += count
            self.usage_data["monthly_usage"][self.current_month]["last_request"] = datetime.now().isoformat()
            
            # Update daily breakdown
            today = datetime.now().strftime("%Y-%m-%d")
            daily_breakdown = self.usage_data["monthly_usage"][self.current_month]["daily_breakdown"]
            daily_breakdown[today] = daily_breakdown.get(today, 0) + count
            
            # Update all-time stats
            self.usage_data["all_time_stats"]["total_requests"] += count
            if not self.usage_data["all_time_stats"]["first_request"]:
                self.usage_data["all_time_stats"]["first_request"] = datetime.now().isoformat()
            self.usage_data["all_time_stats"]["last_request"] = datetime.now().isoformat()
            
            # Save changes
            success = self._save_usage_data()
            if success:
                self.logger.info(f"Incremented usage by {count}. Current month: {self.get_current_month_usage()}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error incrementing usage: {e}")
            return False
    
    def get_current_month_usage(self) -> int:
        """
        Get API usage count for current month.
        
        Returns:
            int: Number of API requests this month
        """
        return self.usage_data["monthly_usage"].get(self.current_month, {}).get("count", 0)
    
    def get_previous_month_usage(self) -> int:
        """
        Get API usage count for previous month.
        
        Returns:
            int: Number of API requests last month
        """
        current_date = datetime.now()
        prev_month = (current_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        return self.usage_data["monthly_usage"].get(prev_month, {}).get("count", 0)
    
    def get_all_time_usage(self) -> int:
        """
        Get total API usage across all months.
        
        Returns:
            int: Total number of API requests
        """
        return self.usage_data["all_time_stats"].get("total_requests", 0)
    
    def get_monthly_usage(self, year_month: str) -> Optional[int]:
        """
        Get usage for a specific month.
        
        Args:
            year_month: Month in "YYYY-MM" format
            
        Returns:
            Optional[int]: Usage count for specified month, None if month doesn't exist
        """
        return self.usage_data["monthly_usage"].get(year_month, {}).get("count")
    
    def get_current_month_daily_breakdown(self) -> Dict[str, int]:
        """
        Get daily breakdown for current month.
        
        Returns:
            Dict: Daily usage counts for current month
        """
        return self.usage_data["monthly_usage"].get(self.current_month, {}).get("daily_breakdown", {})
    
    def get_usage_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Get usage trend for the last N months.
        
        Args:
            months: Number of months to include
            
        Returns:
            List: Usage data for last N months
        """
        trend = []
        current_date = datetime.now()
        
        for i in range(months):
            month_date = current_date - timedelta(days=30 * i)
            month_key = month_date.strftime("%Y-%m")
            usage = self.get_monthly_usage(month_key) or 0
            
            trend.append({
                "month": month_key,
                "usage": usage,
                "month_name": month_date.strftime("%B %Y")
            })
        
        return list(reversed(trend))  # Return in chronological order
    
    def _calculate_daily_average(self) -> float:
        """
        Calculate daily average for current month.
        
        Returns:
            float: Daily average usage
        """
        current_usage = self.get_current_month_usage()
        current_date = datetime.now()
        
        # Get days in current month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)
        
        days_in_month = (next_month - timedelta(days=1)).day
        days_passed = current_date.day
        
        if days_passed == 0:
            return 0.0
        
        return round(current_usage / days_passed, 2)
    
    def _calculate_projected_monthly(self) -> int:
        """
        Calculate projected usage for current month.
        
        Returns:
            int: Projected monthly usage
        """
        current_usage = self.get_current_month_usage()
        current_date = datetime.now()
        
        # Get days in current month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)
        
        days_in_month = (next_month - timedelta(days=1)).day
        days_passed = current_date.day
        
        if days_passed == 0:
            return current_usage
        
        daily_average = current_usage / days_passed
        return int(daily_average * days_in_month)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.
        
        Returns:
            Dict: Comprehensive usage statistics
        """
        current_usage = self.get_current_month_usage()
        previous_usage = self.get_previous_month_usage()
        all_time_usage = self.get_all_time_usage()
        daily_average = self._calculate_daily_average()
        projected_monthly = self._calculate_projected_monthly()
        
        # Calculate usage change from previous month
        if previous_usage > 0:
            usage_change = ((current_usage - previous_usage) / previous_usage) * 100
        else:
            usage_change = 0.0 if current_usage == 0 else 100.0
        
        return {
            "current_month": self.current_month,
            "current_month_usage": current_usage,
            "previous_month_usage": previous_usage,
            "all_time_usage": all_time_usage,
            "daily_average": daily_average,
            "projected_monthly": projected_monthly,
            "usage_change_percent": round(usage_change, 1),
            "daily_breakdown": self.get_current_month_daily_breakdown(),
            "usage_trend": self.get_usage_trend(6),
            "first_request": self.usage_data["all_time_stats"].get("first_request"),
            "last_request": self.usage_data["all_time_stats"].get("last_request")
        }
    
    def reset_current_month(self) -> bool:
        """
        Reset current month counter.
        
        Returns:
            bool: True if successful
        """
        try:
            if self.current_month in self.usage_data["monthly_usage"]:
                # Store reset history
                if "reset_history" not in self.usage_data:
                    self.usage_data["reset_history"] = []
                
                self.usage_data["reset_history"].append({
                    "month": self.current_month,
                    "previous_count": self.usage_data["monthly_usage"][self.current_month]["count"],
                    "reset_at": datetime.now().isoformat()
                })
                
                # Reset current month
                self.usage_data["monthly_usage"][self.current_month] = {
                    "count": 0,
                    "first_request": datetime.now().isoformat(),
                    "last_request": None,
                    "daily_breakdown": {}
                }
                
                success = self._save_usage_data()
                if success:
                    self.logger.info(f"Reset usage counter for {self.current_month}")
                return success
            return False
            
        except Exception as e:
            self.logger.error(f"Error resetting current month: {e}")
            return False
    
    def reset_all_usage(self) -> bool:
        """
        Reset all usage data (use with caution).
        
        Returns:
            bool: True if successful
        """
        try:
            # Store backup before reset
            backup_data = self.usage_data.copy()
            
            # Reset to default
            self.usage_data = self._get_default_usage_data()
            self._ensure_current_month()
            
            # Save reset history
            self.usage_data["reset_history"] = [{
                "type": "full_reset",
                "previous_total": backup_data["all_time_stats"].get("total_requests", 0),
                "reset_at": datetime.now().isoformat()
            }]
            
            success = self._save_usage_data()
            if success:
                self.logger.warning("All usage data has been reset")
            return success
            
        except Exception as e:
            self.logger.error(f"Error resetting all usage: {e}")
            return False
    
    def export_usage_data(self, export_path: Path) -> bool:
        """
        Export usage data to a file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Usage data exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting usage data: {e}")
            return False
    
    def import_usage_data(self, import_path: Path) -> bool:
        """
        Import usage data from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Validate imported data structure
            if "monthly_usage" in imported_data and "all_time_stats" in imported_data:
                self.usage_data = imported_data
                success = self._save_usage_data()
                if success:
                    self.logger.info(f"Usage data imported from {import_path}")
                return success
            else:
                self.logger.error("Invalid usage data format in import file")
                return False
                
        except Exception as e:
            self.logger.error(f"Error importing usage data: {e}")
            return False
    
    def get_usage_alerts(self, warning_threshold: int = 800, critical_threshold: int = 950) -> List[Dict[str, Any]]:
        """
        Get usage alerts based on thresholds.
        
        Args:
            warning_threshold: Warning threshold (default 800)
            critical_threshold: Critical threshold (default 950)
            
        Returns:
            List: Usage alerts
        """
        alerts = []
        current_usage = self.get_current_month_usage()
        daily_average = self._calculate_daily_average()
        projected_monthly = self._calculate_projected_monthly()
        
        # Check thresholds
        if current_usage >= critical_threshold:
            alerts.append({
                "level": "critical",
                "message": f"Critical: Monthly usage ({current_usage}) exceeds critical threshold ({critical_threshold})",
                "current_usage": current_usage,
                "threshold": critical_threshold
            })
        elif current_usage >= warning_threshold:
            alerts.append({
                "level": "warning",
                "message": f"Warning: Monthly usage ({current_usage}) exceeds warning threshold ({warning_threshold})",
                "current_usage": current_usage,
                "threshold": warning_threshold
            })
        
        # Check projection
        if projected_monthly > 1000:
            alerts.append({
                "level": "info",
                "message": f"Projected monthly usage: {projected_monthly} requests",
                "projected_usage": projected_monthly
            })
        
        return alerts
    
    def __str__(self) -> str:
        """String representation."""
        stats = self.get_usage_stats()
        return f"UsageTracker(current_month={stats['current_month']}, usage={stats['current_month_usage']}, total={stats['all_time_usage']})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"UsageTracker(storage_file='{self.storage_file}', current_month='{self.current_month}')"


# Global instance for easy access
_global_tracker = None

def get_usage_tracker(storage_file: str = "api_usage.json") -> UsageTracker:
    """
    Get global usage tracker instance (singleton pattern).
    
    Args:
        storage_file: Usage data storage file name
        
    Returns:
        UsageTracker: Global usage tracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = UsageTracker(storage_file)
    return _global_tracker


def track_usage(count: int = 1, storage_file: str = "api_usage.json") -> bool:
    """
    Convenience function to track API usage.
    
    Args:
        count: Number of requests to track
        storage_file: Usage data storage file name
        
    Returns:
        bool: True if successful
    """
    tracker = get_usage_tracker(storage_file)
    return tracker.increment_usage(count)


def get_usage_statistics(storage_file: str = "api_usage.json") -> Dict[str, Any]:
    """
    Convenience function to get usage statistics.
    
    Args:
        storage_file: Usage data storage file name
        
    Returns:
        Dict: Usage statistics
    """
    tracker = get_usage_tracker(storage_file)
    return tracker.get_usage_stats()


if __name__ == "__main__":
    # Test the usage tracker
    print("Testing UsageTracker...")
    
    # Create a test instance
    tracker = UsageTracker("test_usage.json")
    
    # Test incrementing usage
    tracker.increment_usage(5)
    tracker.increment_usage(3)
    
    # Test getting statistics
    stats = tracker.get_usage_stats()
    print(f"Current month usage: {stats['current_month_usage']}")
    print(f"All time usage: {stats['all_time_usage']}")
    print(f"Daily average: {stats['daily_average']}")
    
    # Test alerts
    alerts = tracker.get_usage_alerts(warning_threshold=5, critical_threshold=8)
    for alert in alerts:
        print(f"Alert: {alert['level']} - {alert['message']}")
    
    # Clean up test file
    if tracker.storage_file.exists():
        tracker.storage_file.unlink()
    
    print("UsageTracker test completed!")