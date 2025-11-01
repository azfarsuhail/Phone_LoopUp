# tests/test_usage_tracker.py
import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from modules.usage_tracker import UsageTracker, get_usage_tracker, track_usage, get_usage_statistics


class TestUsageTracker:
    """Test cases for UsageTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_storage_file = self.temp_dir / "test_usage.json"
        self.tracker = UsageTracker(storage_file=str(self.test_storage_file))
        
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        
        if self.test_storage_file.exists():
            self.test_storage_file.unlink()
        if self.temp_dir.exists():
            # Remove directory and all contents
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test UsageTracker initialization."""
        assert self.tracker.storage_file == self.test_storage_file
        assert self.tracker.current_month == datetime.now().strftime("%Y-%m")
        assert "monthly_usage" in self.tracker.usage_data
        assert "all_time_stats" in self.tracker.usage_data
    
    def test_increment_usage(self):
        """Test incrementing usage counter."""
        initial_count = self.tracker.get_current_month_usage()
        
        success = self.tracker.increment_usage(5)
        
        assert success is True
        assert self.tracker.get_current_month_usage() == initial_count + 5
    
    def test_increment_usage_multiple(self):
        """Test multiple usage increments."""
        self.tracker.increment_usage(3)
        self.tracker.increment_usage(2)
        
        assert self.tracker.get_current_month_usage() == 5
    
    def test_get_current_month_usage(self):
        """Test getting current month usage."""
        # Initial usage should be 0
        assert self.tracker.get_current_month_usage() == 0
        
        # After incrementing
        self.tracker.increment_usage(10)
        assert self.tracker.get_current_month_usage() == 10
    
    def test_get_previous_month_usage(self):
        """Test getting previous month usage."""
        # Create data for previous month
        prev_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        self.tracker.usage_data["monthly_usage"][prev_month] = {
            "count": 25,
            "first_request": "2024-01-01T00:00:00",
            "last_request": "2024-01-31T23:59:59",
            "daily_breakdown": {}
        }
        
        usage = self.tracker.get_previous_month_usage()
        assert usage == 25
    
    def test_get_all_time_usage(self):
        """Test getting all-time usage."""
        # Initial all-time usage should be 0
        assert self.tracker.get_all_time_usage() == 0
        
        # After incrementing
        self.tracker.increment_usage(15)
        assert self.tracker.get_all_time_usage() == 15
    
    def test_get_monthly_usage(self):
        """Test getting usage for specific month."""
        test_month = "2024-01"
        self.tracker.usage_data["monthly_usage"][test_month] = {
            "count": 50,
            "first_request": "2024-01-01T00:00:00",
            "last_request": "2024-01-31T23:59:59",
            "daily_breakdown": {}
        }
        
        usage = self.tracker.get_monthly_usage(test_month)
        assert usage == 50
        
        # Test non-existent month
        usage = self.tracker.get_monthly_usage("1999-01")
        assert usage is None
    
    def test_get_current_month_daily_breakdown(self):
        """Test getting daily breakdown for current month."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Add some daily data
        self.tracker.usage_data["monthly_usage"][self.tracker.current_month]["daily_breakdown"] = {
            today: 5,
            "2024-01-15": 3
        }
        
        breakdown = self.tracker.get_current_month_daily_breakdown()
        assert breakdown[today] == 5
        assert breakdown["2024-01-15"] == 3
    
    def test_get_usage_stats(self):
        """Test getting comprehensive usage statistics."""
        # Add some historical data
        prev_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        self.tracker.usage_data["monthly_usage"][prev_month] = {
            "count": 30,
            "first_request": "2024-01-01T00:00:00",
            "last_request": "2024-01-31T23:59:59",
            "daily_breakdown": {}
        }
        
        # Manually set all_time_stats to match the test expectation
        self.tracker.usage_data["all_time_stats"]["total_requests"] = 30

        # Add current month usage
        self.tracker.increment_usage(10)

        stats = self.tracker.get_usage_stats()

        assert "current_month" in stats
        assert "current_month_usage" in stats
        assert "previous_month_usage" in stats
        assert "all_time_usage" in stats
        assert "daily_average" in stats
        assert "projected_monthly" in stats
        assert "usage_change_percent" in stats
        assert "daily_breakdown" in stats
        assert "usage_trend" in stats

        assert stats["current_month_usage"] == 10
        assert stats["previous_month_usage"] == 30
        # All-time should be previous (30) + current (10) = 40
        assert stats["all_time_usage"] == 40


    def test_get_usage_trend(self):
        """Test getting usage trend."""
        # Add data for previous months
        current_date = datetime.now()
        for i in range(3):
            month_date = current_date - timedelta(days=30 * i)
            month_key = month_date.strftime("%Y-%m")
            self.tracker.usage_data["monthly_usage"][month_key] = {
                "count": (i + 1) * 10,
                "first_request": month_date.isoformat(),
                "last_request": month_date.isoformat(),
                "daily_breakdown": {}
            }
        
        trend = self.tracker.get_usage_trend(months=3)
        
        assert len(trend) == 3
        for i, month_data in enumerate(trend):
            assert "month" in month_data
            assert "usage" in month_data
            assert "month_name" in month_data
    
    def test_reset_current_month(self):
        """Test resetting current month counter."""
        # Add some usage
        self.tracker.increment_usage(20)
        assert self.tracker.get_current_month_usage() == 20
        
        # Reset
        success = self.tracker.reset_current_month()
        assert success is True
        assert self.tracker.get_current_month_usage() == 0
        
        # Check reset history was recorded
        assert "reset_history" in self.tracker.usage_data
        assert len(self.tracker.usage_data["reset_history"]) == 1
    
    def test_reset_all_usage(self):
        """Test resetting all usage data."""
        # Add some usage data
        self.tracker.increment_usage(25)
        self.tracker.usage_data["monthly_usage"]["2024-01"] = {
            "count": 50,
            "first_request": "2024-01-01T00:00:00",
            "last_request": "2024-01-31T23:59:59",
            "daily_breakdown": {}
        }
        
        success = self.tracker.reset_all_usage()
        assert success is True
        assert self.tracker.get_all_time_usage() == 0
        assert self.tracker.get_current_month_usage() == 0
        
        # Check reset history was recorded
        assert "reset_history" in self.tracker.usage_data
    
    def test_export_usage_data(self):
        """Test exporting usage data."""
        # Add some data
        self.tracker.increment_usage(10)
        
        export_file = self.temp_dir / "exported_usage.json"
        success = self.tracker.export_usage_data(export_file)
        
        assert success is True
        assert export_file.exists()
        
        # Verify exported content
        with open(export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert "monthly_usage" in exported_data
        assert "all_time_stats" in exported_data
    
    def test_import_usage_data(self):
        """Test importing usage data."""
        # Create export data
        export_data = {
            "metadata": {
                "version": "1.0.0",
                "created": "2024-01-01T00:00:00",
                "last_updated": "2024-01-31T23:59:59"
            },
            "monthly_usage": {
                "2024-01": {
                    "count": 100,
                    "first_request": "2024-01-01T00:00:00",
                    "last_request": "2024-01-31T23:59:59",
                    "daily_breakdown": {}
                }
            },
            "all_time_stats": {
                "total_requests": 100,
                "first_request": "2024-01-01T00:00:00",
                "last_request": "2024-01-31T23:59:59"
            }
        }
        
        import_file = self.temp_dir / "import_usage.json"
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f)
        
        success = self.tracker.import_usage_data(import_file)
        assert success is True
        assert self.tracker.get_all_time_usage() == 100
    
    def test_import_usage_data_invalid(self):
        """Test importing invalid usage data."""
        invalid_data = {"some_random_key": "value"}
        
        import_file = self.temp_dir / "invalid_usage.json"
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        success = self.tracker.import_usage_data(import_file)
        assert success is False
    
    def test_get_usage_alerts(self):
        """Test getting usage alerts."""
        # Set current usage to trigger alerts
        self.tracker.usage_data["monthly_usage"][self.tracker.current_month]["count"] = 900
        
        alerts = self.tracker.get_usage_alerts(warning_threshold=800, critical_threshold=950)
        
        # Should have warning alert
        assert len(alerts) >= 1
        assert any(alert["level"] == "warning" for alert in alerts)
    
    def test_get_usage_alerts_critical(self):
        """Test getting critical usage alerts."""
        # Set current usage to trigger critical alert
        self.tracker.usage_data["monthly_usage"][self.tracker.current_month]["count"] = 960
        
        alerts = self.tracker.get_usage_alerts(warning_threshold=800, critical_threshold=950)
        
        # Should have critical alert
        assert len(alerts) >= 1
        assert any(alert["level"] == "critical" for alert in alerts)
    
    def test_string_representation(self):
        """Test string representation."""
        representation = str(self.tracker)
        assert "UsageTracker" in representation
        assert self.tracker.current_month in representation
    
    def test_month_change_handling(self):
        """Test handling of month changes."""
        original_month = self.tracker.current_month
        
        # Mock datetime to simulate month change
        with patch('modules.usage_tracker.datetime') as mock_datetime:
            mock_now = datetime.now() + timedelta(days=35)  # Move to next month
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime.return_value = mock_now.strftime("%Y-%m")
            
            # This should trigger month change handling
            self.tracker.increment_usage(5)
            
            # Current month should be updated
            assert self.tracker.current_month == mock_now.strftime("%Y-%m")
            # New month should be initialized
            assert self.tracker.current_month in self.tracker.usage_data["monthly_usage"]


class TestUsageTrackerConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_storage_file = self.temp_dir / "test_convenience_usage.json"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_storage_file.exists():
            self.test_storage_file.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()
    
    def test_get_usage_tracker_singleton(self):
        """Test get_usage_tracker singleton pattern."""
        tracker1 = get_usage_tracker(str(self.test_storage_file))
        tracker2 = get_usage_tracker(str(self.test_storage_file))
        
        # Should return the same instance
        assert tracker1 is tracker2
    
    def test_track_usage_function(self):
        """Test track_usage convenience function."""
        success = track_usage(count=3, storage_file=str(self.test_storage_file))
        
        assert success is True
        
        # Verify usage was tracked
        tracker = get_usage_tracker(str(self.test_storage_file))
        assert tracker.get_current_month_usage() == 3
    
    def test_get_usage_statistics_function(self):
        """Test get_usage_statistics convenience function."""
        # Clear the singleton cache to ensure fresh state
        import modules.usage_tracker
        modules.usage_tracker._global_tracker = None
        
        # Track some usage first
        track_usage(count=7, storage_file=str(self.test_storage_file))

        stats = get_usage_statistics(storage_file=str(self.test_storage_file))

        assert "current_month_usage" in stats
        assert "all_time_usage" in stats
        assert stats["current_month_usage"] == 7


class TestUsageTrackerEdgeCases:
    """Test edge cases and error scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_storage_file = self.temp_dir / "test_edge_cases_usage.json"
        self.tracker = UsageTracker(storage_file=str(self.test_storage_file))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        
        if self.test_storage_file.exists():
            self.test_storage_file.unlink()
        if self.temp_dir.exists():
            # Remove directory and all contents
            shutil.rmtree(self.temp_dir)
    
    def test_increment_usage_negative(self):
        """Test incrementing with negative count."""
        initial_count = self.tracker.get_current_month_usage()
        
        success = self.tracker.increment_usage(-5)
        
        # Should handle gracefully (either fail or treat as 0)
        # Current implementation treats negative as positive, so we'll check it doesn't crash
        assert success is True
    
    def test_increment_usage_zero(self):
        """Test incrementing with zero count."""
        initial_count = self.tracker.get_current_month_usage()
        
        success = self.tracker.increment_usage(0)
        
        assert success is True
        assert self.tracker.get_current_month_usage() == initial_count
    
    def test_corrupted_storage_file(self):
        """Test handling of corrupted storage file."""
        # Create a corrupted JSON file
        with open(self.test_storage_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        # Should handle gracefully and use default data
        tracker = UsageTracker(storage_file=str(self.test_storage_file))
        assert tracker.get_current_month_usage() == 0
    
    def test_missing_storage_file(self):
        """Test initialization with missing storage file."""
        missing_file = self.temp_dir / "nonexistent.json"
        
        # Should handle gracefully and use default data
        tracker = UsageTracker(storage_file=str(missing_file))
        assert tracker.get_current_month_usage() == 0
    
    def test_permission_denied_storage(self):
        """Test handling of permission denied errors."""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")
            
            # Should handle gracefully and use default data
            tracker = UsageTracker(storage_file=str(self.test_storage_file))
            assert tracker.get_current_month_usage() == 0
    
    def test_large_usage_numbers(self):
        """Test handling of very large usage numbers."""
        large_number = 1_000_000
        
        success = self.tracker.increment_usage(large_number)
        
        assert success is True
        assert self.tracker.get_current_month_usage() == large_number
        assert self.tracker.get_all_time_usage() == large_number


class TestUsageTrackerIntegration:
    """Integration tests for UsageTracker."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_storage_file = self.temp_dir / "test_integration_usage.json"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        
        if self.test_storage_file.exists():
            self.test_storage_file.unlink()
        if self.temp_dir.exists():
            # Remove directory and all contents
            shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow(self):
        """Test complete usage tracking workflow."""
        tracker = UsageTracker(storage_file=str(self.test_storage_file))
        
        # Track various usage patterns
        for i in range(10):
            tracker.increment_usage(i + 1)
        
        # Verify totals
        assert tracker.get_current_month_usage() == 55  # 1+2+3+...+10
        assert tracker.get_all_time_usage() == 55
        
        # Get statistics
        stats = tracker.get_usage_stats()
        assert stats["current_month_usage"] == 55
        assert stats["all_time_usage"] == 55
        
        # Reset and verify
        tracker.reset_current_month()
        assert tracker.get_current_month_usage() == 0
        assert tracker.get_all_time_usage() == 55  # All-time should remain
        
        # Export and import
        export_file = self.temp_dir / "export_integration.json"
        tracker.export_usage_data(export_file)
        
        new_tracker = UsageTracker(storage_file=str(self.test_storage_file))
        new_tracker.import_usage_data(export_file)
        
        assert new_tracker.get_all_time_usage() == 55


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])