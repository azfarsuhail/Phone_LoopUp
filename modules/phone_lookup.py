# modules/phone_lookup.py
import pandas as pd
import requests
import time
import os
from datetime import datetime
import re
import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from pathlib import Path
import logging

from .usage_tracker import get_usage_tracker
from .path_utils import get_logs_path, get_data_path


class PhoneLookup:
    """
    Phone number lookup functionality using Eyecon API.
    Handles API communication, data processing, and result management.
    """
    
    def __init__(self):
        self.is_running = False
        self.config = {}
        self.callbacks = {}
        self.usage_tracker = get_usage_tracker()  # Use the global tracker
        self.session = None
        self.current_df = None
        self.processed_count = 0
        self.error_count = 0
        
        # Track max columns for dynamic expansion
        self.max_names = 0
        self.max_images = 0
        self.max_base64_images = 0
        
        # Setup module-specific logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup module-specific logger."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            log_file = get_logs_path() / "phone_lookup.log"
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def configure(self, 
                  input_file: str, 
                  output_file: str, 
                  api_key: str,
                  api_host: str = "eyecon.p.rapidapi.com",
                  delay: float = 1.5, 
                  save_interval: int = 10,
                  max_retries: int = 3,
                  timeout: int = 30,
                  log_callback: Callable = None,
                  status_callback: Callable = None, 
                  progress_callback: Callable = None,
                  usage_callback: Callable = None,
                  stop_callback: Callable = None) -> None:
        """
        Configure the phone lookup module.
        
        Args:
            input_file: Path to input Excel file
            output_file: Path to output Excel file
            api_key: RapidAPI key
            api_host: API host URL
            delay: Delay between requests in seconds
            save_interval: Save progress every N requests
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            log_callback: Callback for log messages
            status_callback: Callback for status updates
            progress_callback: Callback for progress updates
            usage_callback: Callback for usage updates
            stop_callback: Callback to check if processing should stop
        """
        self.config = {
            'input_file': input_file,
            'output_file': output_file,
            'api_key': api_key,
            'api_host': api_host,
            'delay': delay,
            'save_interval': save_interval,
            'max_retries': max_retries,
            'timeout': timeout,
            'api_url': f"https://{api_host}/api/v1/search"
        }
        
        self.callbacks = {
            'log': log_callback,
            'status': status_callback,
            'progress': progress_callback,
            'usage': usage_callback,
            'stop': stop_callback
        }
        
        # Reset max columns
        self.max_names = 0
        self.max_images = 0
        self.max_base64_images = 0
        
        # Initialize requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'x-rapidapi-host': api_host,
            'x-rapidapi-key': api_key,
            'User-Agent': 'PhoneLookupTool/1.0.0'
        })
        
        self.logger.info(f"PhoneLookup configured: input={input_file}, output={output_file}")
        self.log("Phone lookup module configured successfully")
    
    def should_stop(self) -> bool:
        """Check if processing should stop."""
        if self.callbacks.get('stop'):
            return self.callbacks['stop']()
        return False
    
    def log(self, message: str, level: str = "info") -> None:
        """Log message to both file and callback."""
        # Log to file
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        
        # Send to callback
        if self.callbacks.get('log'):
            self.callbacks['log'](message)
    
    def update_status(self, message: str) -> None:
        """Update status message."""
        if self.callbacks.get('status'):
            self.callbacks['status'](message)
    
    def update_progress(self, value: float) -> None:
        """Update progress percentage."""
        if self.callbacks.get('progress'):
            self.callbacks['progress'](value)
    
    def update_usage(self) -> None:
        """Update usage statistics."""
        if self.callbacks.get('usage'):
            stats = self.usage_tracker.get_usage_stats()
            self.callbacks['usage'](stats)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return self.usage_tracker.get_usage_stats()
    
    # NEW: Manual usage editing methods that call the usage tracker
    def set_usage_count(self, count: int, month: str = None) -> bool:
        """
        Manually set the usage count.
        
        Args:
            count: New usage count value
            month: Month in "YYYY-MM" format (defaults to current month)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.usage_tracker.set_usage_count(count, month)
            if success:
                self.log(f"Manually set usage count to: {count} for month: {month or 'current'}")
                self.update_usage()
            return success
        except Exception as e:
            self.log(f"Error setting usage count: {str(e)}", "error")
            return False
    
    def add_usage(self, count: int, month: str = None) -> bool:
        """
        Manually add to usage count.
        
        Args:
            count: Number to add to current usage
            month: Month in "YYYY-MM" format (defaults to current month)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.usage_tracker.add_usage(count, month)
            if success:
                action = "added" if count >= 0 else "subtracted"
                self.log(f"Manually {action} {abs(count)} to usage for month: {month or 'current'}")
                self.update_usage()
            return success
        except Exception as e:
            self.log(f"Error adding usage: {str(e)}", "error")
            return False
    
    def reset_usage(self, month: str = None) -> bool:
        """
        Reset usage count to zero.
        
        Args:
            month: Month in "YYYY-MM" format (defaults to current month)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.usage_tracker.reset_monthly_usage(month)
            if success:
                self.log(f"Manually reset usage for month: {month or 'current'}")
                self.update_usage()
            return success
        except Exception as e:
            self.log(f"Error resetting usage: {str(e)}", "error")
            return False
    
    def get_available_months(self) -> List[str]:
        """
        Get list of available months with usage data.
        
        Returns:
            List[str]: Sorted list of months
        """
        return self.usage_tracker.get_available_months()
    
    def run(self) -> bool:
        """
        Run the phone lookup process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.is_running = True
        self.processed_count = 0
        self.error_count = 0
        
        try:
            self.log("Starting phone lookup process")
            success = self._perform_lookup()
            
            if success:
                self.log(f"Phone lookup completed successfully. Processed: {self.processed_count}, Errors: {self.error_count}")
            else:
                self.log(f"Phone lookup completed with issues. Processed: {self.processed_count}, Errors: {self.error_count}")
            
            return success
            
        except Exception as e:
            error_msg = f"Unexpected error in phone lookup: {str(e)}"
            self.log(error_msg, "error")
            self.update_status("Processing failed with unexpected error")
            return False
            
        finally:
            self.is_running = False
            # Close session
            if self.session:
                self.session.close()
    
    def stop(self) -> None:
        """Stop the phone lookup process."""
        self.is_running = False
        self.log("Stop signal received")
    
    def _perform_lookup(self) -> bool:
        """Perform the actual phone number lookup process."""
        try:
            # Step 1: Load and validate input file
            self.update_status("Loading input file...")
            df = self._load_input_file()
            if df is None:
                return False
            
            total_numbers = len(df)
            self.log(f"Loaded {total_numbers} phone numbers for processing")
            
            # Step 2: Initialize results dataframe
            self.current_df = self._initialize_results_df(df)
            
            # Step 3: Process each phone number
            self.update_status("Starting API lookups...")
            self.log(f"Beginning processing of {total_numbers} numbers")
            
            for idx, row in df.iterrows():
                if self.should_stop():
                    self.log("Processing stopped by user")
                    return False
                
                number = str(row['Number']).strip()
                self._process_single_number(idx, number, total_numbers)
            
            # Step 4: Final save and completion
            if not self.should_stop():
                self._save_results(final=True)
                self.update_status("Phone lookup completed successfully")
                return True
            else:
                self.update_status("Processing stopped")
                return False
                
        except Exception as e:
            self.log(f"Error during phone lookup processing: {str(e)}", "error")
            return False
    
    def _load_input_file(self) -> Optional[pd.DataFrame]:
        """Load and validate the input Excel file."""
        try:
            df = pd.read_excel(self.config['input_file'])
            
            # Validate required columns
            if 'Number' not in df.columns:
                error_msg = "Input file must contain a 'Number' column"
                self.log(error_msg, "error")
                self.update_status("Error: Missing 'Number' column")
                return None
            
            # Clean and validate phone numbers
            df = self._clean_phone_numbers(df)
            
            # Log file statistics
            valid_numbers = len(df)
            self.log(f"Input file loaded: {valid_numbers} valid phone numbers")
            
            return df
            
        except Exception as e:
            error_msg = f"Error loading input file: {str(e)}"
            self.log(error_msg, "error")
            self.update_status("Error loading input file")
            return None
    
    def _clean_phone_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate phone numbers in the dataframe."""
        def clean_number(number):
            if pd.isna(number):
                return None
            
            # Convert to string and remove non-digit characters except +
            cleaned = re.sub(r'[^\d+]', '', str(number))
            
            # Remove leading zeros and country code adjustments
            if cleaned.startswith('0'):
                cleaned = '92' + cleaned[1:]  # Pakistani format
            elif cleaned.startswith('+92'):
                cleaned = '92' + cleaned[3:]
            elif cleaned.startswith('92'):
                cleaned = cleaned
            else:
                # Assume it's already in correct format
                cleaned = cleaned
            
            # Validate length
            if len(cleaned) < 10 or len(cleaned) > 15:
                return None
            
            return cleaned
        
        # Apply cleaning and filter out invalid numbers
        df['Cleaned_Number'] = df['Number'].apply(clean_number)
        df = df[df['Cleaned_Number'].notna()].copy()
        df = df.reset_index(drop=True)
        
        return df
    
    def _initialize_results_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Initialize the results dataframe with required columns."""
        results_df = df.copy()
        
        # Add basic result columns
        result_columns = [
            'Lookup_Status',
            'Full_Name',  # This will be Name_1
            'Lookup_Timestamp',
            'Error_Message'
        ]
        
        for col in result_columns:
            if col not in results_df.columns:
                results_df[col] = ""
        
        # We'll dynamically add Name_X, Image_X, and b64_X columns as we process data
        return results_df
    
    def _process_single_number(self, idx: int, number: str, total_numbers: int) -> None:
        """Process a single phone number."""
        try:
            # Update progress
            progress = (idx + 1) / total_numbers * 100
            self.update_progress(progress)
            self.update_status(f"Processing {idx + 1}/{total_numbers}: {number}")
            
            # Perform API lookup
            result = self._lookup_phone_number(number)
            
            # Update results with wide format
            self._update_results_wide_format(idx, result)
            self.processed_count += 1
            
            # Update usage counter - ONLY if the lookup was successful
            if result.get('status') == 'Success':
                self.usage_tracker.increment_usage(1)
                self.update_usage()
            
            # Save progress periodically
            if (idx + 1) % self.config['save_interval'] == 0:
                self._save_results()
                self.log(f"Progress saved: {idx + 1}/{total_numbers} numbers processed")
            
            # Rate limiting
            if idx < total_numbers - 1:  # Don't delay after last number
                time.sleep(self.config['delay'])
                
        except Exception as e:
            self.error_count += 1
            error_msg = f"Error processing number {number}: {str(e)}"
            self.log(error_msg, "error")
    
    def _lookup_phone_number(self, number: str) -> Dict[str, Any]:
        """
        Look up a phone number using the Eyecon API.
        
        Args:
            number: Phone number to lookup
            
        Returns:
            Dict: Lookup results
        """
        result = {
            "status": "Unknown",
            "full_name": "",
            "other_names": [],
            "image_urls": [],
            "base64_images": [],
            "error_message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        if not number or len(number) < 10:
            result["status"] = "Invalid format"
            result["error_message"] = "Phone number too short"
            return result
        
        try:
            # Parse country code and local number
            country_code, local_number = self._parse_phone_number(number)
            
            params = {
                "code": country_code,
                "number": local_number
            }
            
            self.log(f"API request: {country_code}{local_number}")
            
            # Make API request with retries
            response = self._make_api_request(params)
            
            if response is None:
                result["status"] = "API Error"
                result["error_message"] = "Request failed after retries"
                return result
            
            # Parse response
            data = response.json()
            
            # Check API response status
            if not data.get("status", False):
                result["status"] = f"API Error: {data.get('message', 'Unknown error')}"
                return result
            
            # Extract data from response
            api_data = data.get("data", {})
            result.update(self._extract_api_data(api_data))
            
            self.log(f"  → Found: {len(result['other_names'])} names, {len(result['image_urls'])} images")
            
        except requests.exceptions.Timeout:
            result["status"] = "Error: timeout"
            result["error_message"] = "Request timeout"
        except requests.exceptions.RequestException as e:
            result["status"] = f"Error: {str(e)}"
            result["error_message"] = str(e)
        except json.JSONDecodeError as e:
            result["status"] = "Error: Invalid JSON response"
            result["error_message"] = "Invalid JSON response from API"
        except Exception as e:
            result["status"] = f"Error: {str(e)}"
            result["error_message"] = str(e)
        
        return result
    
    def _parse_phone_number(self, number: str) -> Tuple[str, str]:
        """
        Parse phone number into country code and local number.
        
        Args:
            number: Phone number to parse
            
        Returns:
            Tuple: (country_code, local_number)
        """
        cleaned = str(number).replace(" ", "").replace("-", "")
        
        # Remove leading + if present
        if cleaned.startswith("+"):
            cleaned = cleaned[1:]
        
        # Pakistani number starting with 92
        if cleaned.startswith("92"):
            return "92", cleaned[2:]
        
        # Pakistani number starting with 0
        if cleaned.startswith("0"):
            return "92", cleaned[1:]
        
        # Default: assume it's a Pakistani number without country code
        return "92", cleaned
    
    def _make_api_request(self, params: Dict[str, str]) -> Optional[requests.Response]:
        """
        Make API request with retry logic.
        
        Args:
            params: API parameters
            
        Returns:
            Optional[requests.Response]: API response or None if failed
        """
        max_retries = self.config['max_retries']
        timeout = self.config['timeout']
        
        for attempt in range(max_retries):
            try:
                if self.should_stop():
                    return None
                
                response = self.session.get(
                    self.config['api_url'],
                    params=params,
                    timeout=timeout
                )
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    self.log(f"API request timeout after {max_retries} attempts")
                    return None
                delay = (2 ** attempt)  # Exponential backoff
                self.log(f"API timeout, retrying in {delay}s...")
                time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    self.log(f"API request failed after {max_retries} attempts: {e}")
                    return None
                delay = (2 ** attempt)
                self.log(f"API error: {e}, retrying in {delay}s...")
                time.sleep(delay)
        
        return None
    
    def _extract_api_data(self, api_data: Dict) -> Dict[str, Any]:
        """
        Extract relevant data from API response.
        
        Args:
            api_data: API response data
            
        Returns:
            Dict: Extracted data
        """
        result = {
            "status": "Success",
            "full_name": "",
            "other_names": [],
            "image_urls": [],
            "base64_images": []
        }
        
        # Handle both single object and list of objects
        data_list = []
        if isinstance(api_data, dict):
            data_list = [api_data]
        elif isinstance(api_data, list):
            data_list = api_data
        
        # Extract data from all entries
        for entry in data_list:
            # Extract names
            if "fullName" in entry and entry["fullName"]:
                result["full_name"] = entry["fullName"]
            
            # Extract other names
            if "otherNames" in entry and isinstance(entry["otherNames"], list):
                for other_name in entry["otherNames"]:
                    if isinstance(other_name, dict) and "name" in other_name:
                        name = other_name["name"]
                        if name and name not in result["other_names"]:
                            result["other_names"].append(name)
                    elif isinstance(other_name, str) and other_name:
                        if other_name not in result["other_names"]:
                            result["other_names"].append(other_name)
            
            # Extract images
            if "image" in entry and entry["image"]:
                result["image_urls"].append(entry["image"])
            
            # Extract image arrays
            if "images" in entry and isinstance(entry["images"], list):
                for img_obj in entry["images"]:
                    if isinstance(img_obj, dict) and "pictures" in img_obj:
                        pictures = img_obj["pictures"]
                        if isinstance(pictures, dict):
                            # Get the largest available image
                            for size in sorted(pictures.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True):
                                url = pictures.get(size)
                                if url and url not in result["image_urls"]:
                                    result["image_urls"].append(url)
                                    break
            
            # Extract base64 images
            if "b64" in entry and entry["b64"]:
                result["base64_images"].append(entry["b64"])
        
        # Remove duplicates
        result["other_names"] = list(dict.fromkeys(result["other_names"]))
        result["image_urls"] = list(dict.fromkeys(result["image_urls"]))
        result["base64_images"] = list(dict.fromkeys(result["base64_images"]))
        
        return result
    
    def _update_results_wide_format(self, idx: int, result: Dict[str, Any]) -> None:
        """Update results dataframe with lookup results in wide format."""
        try:
            # Update basic fields
            self.current_df.at[idx, 'Lookup_Status'] = result.get('status', 'Unknown')
            self.current_df.at[idx, 'Lookup_Timestamp'] = result.get('timestamp', '')
            self.current_df.at[idx, 'Error_Message'] = result.get('error_message', '')
            
            # Combine full name with other names for Name_X columns
            all_names = []
            full_name = result.get('full_name', '')
            if full_name:
                all_names.append(full_name)
            
            other_names = result.get('other_names', [])
            all_names.extend(other_names)
            
            # Update max names count
            current_names_count = len(all_names)
            if current_names_count > self.max_names:
                self.max_names = current_names_count
            
            # Add/update Name_X columns
            for i, name in enumerate(all_names, 1):
                col_name = f'Name_{i}'
                if col_name not in self.current_df.columns:
                    # Add new column with empty values for all previous rows
                    self.current_df[col_name] = ""
                self.current_df.at[idx, col_name] = name
            
            # Fill empty Name_X columns for this row
            for i in range(current_names_count + 1, self.max_names + 1):
                col_name = f'Name_{i}'
                if col_name in self.current_df.columns:
                    self.current_df.at[idx, col_name] = ""
            
            # Handle Image URLs
            image_urls = result.get('image_urls', [])
            current_images_count = len(image_urls)
            if current_images_count > self.max_images:
                self.max_images = current_images_count
            
            # Add/update Image_X columns
            for i, image_url in enumerate(image_urls, 1):
                col_name = f'Image_{i}'
                if col_name not in self.current_df.columns:
                    self.current_df[col_name] = ""
                self.current_df.at[idx, col_name] = image_url
            
            # Fill empty Image_X columns for this row
            for i in range(current_images_count + 1, self.max_images + 1):
                col_name = f'Image_{i}'
                if col_name in self.current_df.columns:
                    self.current_df.at[idx, col_name] = ""
            
            # Handle Base64 Images
            base64_images = result.get('base64_images', [])
            current_b64_count = len(base64_images)
            if current_b64_count > self.max_base64_images:
                self.max_base64_images = current_b64_count
            
            # Add/update b64_X columns (truncate long base64 strings for display)
            for i, b64_image in enumerate(base64_images, 1):
                col_name = f'b64_{i}'
                if col_name not in self.current_df.columns:
                    self.current_df[col_name] = ""
                # Store full base64 string
                self.current_df.at[idx, col_name] = b64_image
            
            # Fill empty b64_X columns for this row
            for i in range(current_b64_count + 1, self.max_base64_images + 1):
                col_name = f'b64_{i}'
                if col_name in self.current_df.columns:
                    self.current_df.at[idx, col_name] = ""
                    
        except Exception as e:
            self.log(f"Error updating results for index {idx}: {str(e)}", "error")
    
    def _save_results(self, final: bool = False) -> None:
        """Save results to output file."""
        try:
            if self.current_df is None or self.current_df.empty:
                self.log("No results to save", "warning")
                return
            
            # Make a copy to avoid modifying the original
            save_df = self.current_df.copy()
            
            # Remove temporary columns
            if 'Cleaned_Number' in save_df.columns:
                save_df = save_df.drop('Cleaned_Number', axis=1)
            
            # Ensure consistent column order: Number, Status, Name_X, Image_X, b64_X, Timestamp, Error
            self._reorder_columns(save_df)
            
            # Save to Excel
            save_df.to_excel(self.config['output_file'], index=False)
            
            if final:
                self.log(f"Final results saved to: {self.config['output_file']}")
                self.log(f"Output format: {self.max_names} name columns, {self.max_images} image columns, {self.max_base64_images} base64 columns")
            else:
                self.log(f"Progress saved: {len(save_df)} records")
                
        except Exception as e:
            error_msg = f"Error saving results: {str(e)}"
            self.log(error_msg, "error")
    
    def _reorder_columns(self, df: pd.DataFrame) -> None:
        """Reorder columns to have consistent structure."""
        # Get all columns
        all_columns = list(df.columns)
        
        # Define base columns that should come first
        base_columns = ['Number', 'Lookup_Status']
        
        # Extract dynamic columns
        name_columns = sorted([col for col in all_columns if col.startswith('Name_')], 
                             key=lambda x: int(x.split('_')[1]))
        image_columns = sorted([col for col in all_columns if col.startswith('Image_')], 
                              key=lambda x: int(x.split('_')[1]))
        b64_columns = sorted([col for col in all_columns if col.startswith('b64_')], 
                            key=lambda x: int(x.split('_')[1]))
        
        # Remaining columns (timestamp, error, etc.)
        other_columns = [col for col in all_columns if col not in base_columns + 
                        name_columns + image_columns + b64_columns]
        
        # Reorder the dataframe
        new_order = base_columns + name_columns + image_columns + b64_columns + other_columns
        df = df[new_order]
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "is_running": self.is_running,
            "api_usage": self.usage_tracker.get_usage_stats(),
            "max_names": self.max_names,
            "max_images": self.max_images,
            "max_base64_images": self.max_base64_images
        }
    
    def __str__(self) -> str:
        """String representation."""
        stats = self.get_processing_stats()
        return f"PhoneLookup(processed={stats['processed_count']}, errors={stats['error_count']}, running={stats['is_running']})"


# Utility functions
def validate_phone_number(number: str) -> Tuple[bool, str]:
    """
    Validate phone number format.
    
    Args:
        number: Phone number to validate
        
    Returns:
        Tuple: (is_valid, error_message)
    """
    if pd.isna(number) or not number:
        return False, "Empty phone number"
    
    cleaned = re.sub(r'[^\d+]', '', str(number))
    
    if len(cleaned) < 10:
        return False, "Phone number too short"
    
    if len(cleaned) > 15:
        return False, "Phone number too long"
    
    return True, "Valid"


def batch_lookup_numbers(numbers: List[str], api_key: str, delay: float = 1.0) -> List[Dict]:
    """
    Perform batch lookup of multiple numbers (for external use).
    
    Args:
        numbers: List of phone numbers
        api_key: RapidAPI key
        delay: Delay between requests
        
    Returns:
        List: Lookup results
    """
    lookup = PhoneLookup()
    results = []
    
    for i, number in enumerate(numbers):
        try:
            # Configure for single lookup
            lookup.config = {
                'api_key': api_key,
                'api_host': 'eyecon.p.rapidapi.com',
                'api_url': 'https://eyecon.p.rapidapi.com/api/v1/search',
                'delay': delay
            }
            
            result = lookup._lookup_phone_number(number)
            results.append(result)
            
            # Rate limiting
            if i < len(numbers) - 1:
                time.sleep(delay)
                
        except Exception as e:
            results.append({
                "status": f"Error: {str(e)}",
                "full_name": "",
                "other_names": [],
                "image_urls": [],
                "base64_images": [],
                "error_message": str(e)
            })
    
    return results


if __name__ == "__main__":
    # Test the phone lookup module
    print("Testing PhoneLookup module...")
    
    # Create a test instance
    lookup = PhoneLookup()
    
    # Test configuration
    lookup.configure(
        input_file="test_input.xlsx",
        output_file="test_output.xlsx",
        api_key="test_api_key",
        delay=0.1
    )
    
    print(f"PhoneLookup configured: {lookup}")
    print("Module test completed!")