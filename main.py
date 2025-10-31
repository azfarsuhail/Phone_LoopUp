#!/usr/bin/env python3
"""
Phone Lookup Tool - Main Application
GUI application for phone number lookup and image embedding.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import time
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import sys
import logging

# Add the modules directory to path
sys.path.append(str(Path(__file__).parent))

from modules.phone_lookup import PhoneLookup
from modules.image_embedder import ImageEmbedder
from modules.config_manager import ConfigManager
from modules.usage_tracker import get_usage_tracker
from modules.path_utils import get_logs_path, get_data_path, is_compiled


class SettingsDialog:
    """Settings dialog window for configuration management."""
    
    def __init__(self, parent, config_manager, usage_tracker):
        self.parent = parent
        self.config_manager = config_manager
        self.usage_tracker = usage_tracker
        self.dialog = None
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the settings dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        """Create settings dialog widgets."""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # API Settings Tab
        api_frame = ttk.Frame(notebook, padding="10")
        notebook.add(api_frame, text="API Settings")
        self.create_api_tab(api_frame)
        
        # Processing Settings Tab
        processing_frame = ttk.Frame(notebook, padding="10")
        notebook.add(processing_frame, text="Processing")
        self.create_processing_tab(processing_frame)
        
        # Image Settings Tab
        image_frame = ttk.Frame(notebook, padding="10")
        notebook.add(image_frame, text="Images")
        self.create_image_tab(image_frame)
        
        # UI Settings Tab
        ui_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ui_frame, text="UI")
        self.create_ui_tab(ui_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side='right')
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side='left')
        ttk.Button(button_frame, text="Reset Usage Counter", command=self.reset_usage_counter).pack(side='left', padx=(0, 10))
    
    def create_api_tab(self, parent):
        """Create API settings tab."""
        ttk.Label(parent, text="API Configuration", font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # API Key
        ttk.Label(parent, text="API Key:").grid(row=1, column=0, sticky='w', pady=5)
        self.api_key_var = tk.StringVar()
        api_entry = ttk.Entry(parent, textvariable=self.api_key_var, width=40, show="•")
        api_entry.grid(row=1, column=1, sticky='we', pady=5, padx=(10, 0))
        
        # API Host
        ttk.Label(parent, text="API Host:").grid(row=2, column=0, sticky='w', pady=5)
        self.api_host_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.api_host_var, width=40).grid(row=2, column=1, sticky='we', pady=5, padx=(10, 0))
        
        # Monthly Limit
        ttk.Label(parent, text="Monthly API Limit:").grid(row=3, column=0, sticky='w', pady=5)
        self.monthly_limit_var = tk.IntVar()
        ttk.Spinbox(parent, from_=1, to=100000, textvariable=self.monthly_limit_var, width=15).grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Current Usage
        ttk.Label(parent, text="Current Month Usage:").grid(row=4, column=0, sticky='w', pady=5)
        self.current_usage_var = tk.StringVar(value="0")
        usage_frame = ttk.Frame(parent)
        usage_frame.grid(row=4, column=1, sticky='we', pady=5, padx=(10, 0))
        ttk.Entry(usage_frame, textvariable=self.current_usage_var, width=10, state='readonly').pack(side='left')
        ttk.Button(usage_frame, text="Edit", command=self.edit_usage_counter).pack(side='left', padx=(5, 0))
        
        parent.columnconfigure(1, weight=1)
    
    def create_processing_tab(self, parent):
        """Create processing settings tab."""
        ttk.Label(parent, text="Processing Settings", font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Request Delay
        ttk.Label(parent, text="Request Delay (seconds):").grid(row=1, column=0, sticky='w', pady=5)
        self.delay_var = tk.DoubleVar()
        ttk.Spinbox(parent, from_=0.5, to=10.0, increment=0.1, textvariable=self.delay_var, width=10).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Save Interval
        ttk.Label(parent, text="Save Interval:").grid(row=2, column=0, sticky='w', pady=5)
        self.save_interval_var = tk.IntVar()
        ttk.Spinbox(parent, from_=1, to=1000, textvariable=self.save_interval_var, width=10).grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Max Retries
        ttk.Label(parent, text="Max Retries:").grid(row=3, column=0, sticky='w', pady=5)
        self.max_retries_var = tk.IntVar()
        ttk.Spinbox(parent, from_=1, to=10, textvariable=self.max_retries_var, width=10).grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Country Code
        ttk.Label(parent, text="Default Country Code:").grid(row=4, column=0, sticky='w', pady=5)
        self.country_code_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.country_code_var, width=10).grid(row=4, column=1, sticky='w', pady=5, padx=(10, 0))
        
        parent.columnconfigure(1, weight=1)
    
    def create_image_tab(self, parent):
        """Create image settings tab."""
        ttk.Label(parent, text="Image Settings", font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Max Width
        ttk.Label(parent, text="Max Width (pixels):").grid(row=1, column=0, sticky='w', pady=5)
        self.max_width_var = tk.IntVar()
        ttk.Spinbox(parent, from_=10, to=1000, textvariable=self.max_width_var, width=10).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Max Height
        ttk.Label(parent, text="Max Height (pixels):").grid(row=2, column=0, sticky='w', pady=5)
        self.max_height_var = tk.IntVar()
        ttk.Spinbox(parent, from_=10, to=1000, textvariable=self.max_height_var, width=10).grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Image Quality
        ttk.Label(parent, text="Image Quality (%):").grid(row=3, column=0, sticky='w', pady=5)
        self.image_quality_var = tk.IntVar()
        ttk.Spinbox(parent, from_=1, to=100, textvariable=self.image_quality_var, width=10).grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
        
        parent.columnconfigure(1, weight=1)
    
    def create_ui_tab(self, parent):
        """Create UI settings tab."""
        ttk.Label(parent, text="UI Settings", font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Theme
        ttk.Label(parent, text="Theme:").grid(row=1, column=0, sticky='w', pady=5)
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(parent, textvariable=self.theme_var, values=["system", "light", "dark"], state="readonly", width=15)
        theme_combo.grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Notifications
        self.show_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Show Notifications", variable=self.show_notifications_var).grid(row=2, column=0, columnspan=2, sticky='w', pady=5)
        
        # Auto-open output
        self.auto_open_output_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Auto-open Output Folder", variable=self.auto_open_output_var).grid(row=3, column=0, columnspan=2, sticky='w', pady=5)
        
        parent.columnconfigure(1, weight=1)
    
    def load_current_settings(self):
        """Load current settings into the dialog."""
        # API Settings
        self.api_key_var.set(self.config_manager.get_api_key())
        self.api_host_var.set(self.config_manager.get('api_host', 'eyecon.p.rapidapi.com'))
        self.monthly_limit_var.set(self.config_manager.get('max_requests_per_month', 1000))
        
        # Usage counter
        stats = self.usage_tracker.get_usage_stats()
        self.current_usage_var.set(str(stats['current_month_usage']))
        
        # Processing Settings
        self.delay_var.set(self.config_manager.get('request_delay', 1.5))
        self.save_interval_var.set(self.config_manager.get('save_interval', 10))
        self.max_retries_var.set(self.config_manager.get('max_retries', 3))
        self.country_code_var.set(self.config_manager.get('default_country_code', '92'))
        
        # Image Settings
        self.max_width_var.set(self.config_manager.get('max_image_width', 100))
        self.max_height_var.set(self.config_manager.get('max_image_height', 100))
        self.image_quality_var.set(self.config_manager.get('image_quality', 85))
        
        # UI Settings
        self.theme_var.set(self.config_manager.get('theme', 'system'))
        self.show_notifications_var.set(self.config_manager.get('show_notifications', True))
        self.auto_open_output_var.set(self.config_manager.get('auto_open_output', True))
    
    def save_settings(self):
        """Save settings from dialog."""
        # Validate API key
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "API Key is required!", parent=self.dialog)
            return
        
        # Save settings
        self.config_manager.set_api_key(api_key)
        self.config_manager.set('api_host', self.api_host_var.get())
        self.config_manager.set('max_requests_per_month', self.monthly_limit_var.get())
        self.config_manager.set('request_delay', self.delay_var.get())
        self.config_manager.set('save_interval', self.save_interval_var.get())
        self.config_manager.set('max_retries', self.max_retries_var.get())
        self.config_manager.set('default_country_code', self.country_code_var.get())
        self.config_manager.set('max_image_width', self.max_width_var.get())
        self.config_manager.set('max_image_height', self.max_height_var.get())
        self.config_manager.set('image_quality', self.image_quality_var.get())
        self.config_manager.set('theme', self.theme_var.get())
        self.config_manager.set('show_notifications', self.show_notifications_var.get())
        self.config_manager.set('auto_open_output', self.auto_open_output_var.get())
        
        # Apply theme immediately
        self.parent.apply_theme()
        
        messagebox.showinfo("Success", "Settings saved successfully!", parent=self.dialog)
        self.dialog.destroy()
    
    def reset_to_defaults(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?", parent=self.dialog):
            self.config_manager.reset_to_defaults()
            self.load_current_settings()
            messagebox.showinfo("Success", "Settings reset to defaults!", parent=self.dialog)
    
    def reset_usage_counter(self):
        """Reset usage counter."""
        if messagebox.askyesno("Confirm Reset", "Reset current month usage counter?", parent=self.dialog):
            self.usage_tracker.reset_current_month()
            stats = self.usage_tracker.get_usage_stats()
            self.current_usage_var.set(str(stats['current_month_usage']))
            messagebox.showinfo("Success", "Usage counter reset!", parent=self.dialog)
    
    def edit_usage_counter(self):
        """Edit usage counter manually."""
        current = self.current_usage_var.get()
        new_value = tk.simpledialog.askinteger(
            "Edit Usage Counter", 
            "Enter new usage count:", 
            parent=self.dialog,
            initialvalue=current,
            minvalue=0
        )
        if new_value is not None:
            # This would require modifying the usage tracker to set absolute values
            messagebox.showinfo("Info", "Manual usage editing requires code modification.", parent=self.dialog)


class PhoneLookupApp:
    """Main application class."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Number Lookup Tool")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.usage_tracker = get_usage_tracker()
        self.phone_lookup = PhoneLookup()
        self.image_embedder = ImageEmbedder()
        
        # State variables
        self.current_file = None
        self.is_processing = False
        self.processing_thread = None
        self.stop_requested = False
        
        # Setup logging
        self.setup_logging()
        
        # Create UI
        self.setup_ui()
        
        # Apply theme
        self.apply_theme()
        
        # Check initial configuration
        self.check_initial_config()
        
        # Update usage display
        self.update_usage_display()
    
    def setup_logging(self):
        """Setup application logging."""
        log_file = get_logs_path() / "application.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill='both', expand=True)
        
        # Create menu bar
        self.setup_menu_bar()
        
        # Title
        title_label = ttk.Label(main_frame, text="Phone Number Lookup Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Usage counter section
        self.setup_usage_counter(main_frame)
        
        # File upload section
        self.setup_file_upload(main_frame)
        
        # Progress section
        self.setup_progress_section(main_frame)
        
        # Control buttons
        self.setup_control_buttons(main_frame)
        
        # Log section
        self.setup_log_section(main_frame)
    
    def setup_menu_bar(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File", command=self.browse_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configuration", command=self.show_settings, accelerator="Ctrl+S")
        settings_menu.add_command(label="Reset API Counter", command=self.reset_api_counter)
        
        # Bind shortcuts
        self.root.bind('<Control-o>', lambda e: self.browse_file())
        self.root.bind('<Control-s>', lambda e: self.show_settings())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
    
    def setup_usage_counter(self, parent):
        """Setup the usage counter display."""
        usage_frame = ttk.LabelFrame(parent, text="API Usage Statistics", padding="10")
        usage_frame.pack(fill='x', pady=(0, 20))
        
        # Current month
        ttk.Label(usage_frame, text="Current Month:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.current_month_var = tk.StringVar(value="2024-01")
        ttk.Label(usage_frame, textvariable=self.current_month_var, font=('Arial', 9)).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        # Usage count
        ttk.Label(usage_frame, text="Requests this month:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.usage_count_var = tk.StringVar(value="0")
        self.usage_count_label = ttk.Label(usage_frame, textvariable=self.usage_count_var, font=('Arial', 10, 'bold'))
        self.usage_count_label.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # Daily average
        ttk.Label(usage_frame, text="Daily average:", font=('Arial', 9)).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.daily_avg_var = tk.StringVar(value="0.0")
        ttk.Label(usage_frame, textvariable=self.daily_avg_var).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        # All time total
        ttk.Label(usage_frame, text="All time total:", font=('Arial', 9)).grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.all_time_var = tk.StringVar(value="0")
        ttk.Label(usage_frame, textvariable=self.all_time_var).grid(row=0, column=3, sticky='w', padx=5, pady=2)
        
        # Monthly limit progress
        ttk.Label(usage_frame, text="Monthly Limit:", font=('Arial', 9)).grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.monthly_limit_var = tk.StringVar(value="1000")
        ttk.Label(usage_frame, textvariable=self.monthly_limit_var).grid(row=1, column=3, sticky='w', padx=5, pady=2)
        
        # Usage progress bar
        self.usage_progress = ttk.Progressbar(usage_frame, mode='determinate')
        self.usage_progress.grid(row=3, column=0, columnspan=4, sticky='we', padx=5, pady=5)
        
        # Configure grid weights
        for i in range(4):
            usage_frame.columnconfigure(i, weight=1)
    
    def setup_file_upload(self, parent):
        """Setup file upload section."""
        upload_frame = ttk.LabelFrame(parent, text="Upload Excel File", padding="15")
        upload_frame.pack(fill='x', pady=(0, 20))
        
        # File selection
        file_select_frame = ttk.Frame(upload_frame)
        file_select_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(file_select_frame, text="Select Excel File:").pack(side='left', padx=(0, 10))
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(file_select_frame, text="Browse", command=self.browse_file).pack(side='left')
        
        # File info
        self.file_info_var = tk.StringVar(value="No file selected")
        ttk.Label(upload_frame, textvariable=self.file_info_var, foreground='gray').pack(anchor='w')
    
    def setup_progress_section(self, parent):
        """Setup progress tracking section."""
        progress_frame = ttk.LabelFrame(parent, text="Processing Progress", padding="15")
        progress_frame.pack(fill='x', pady=(0, 20))
        
        # Status
        self.status_var = tk.StringVar(value="Ready to process")
        ttk.Label(progress_frame, textvariable=self.status_var, font=('Arial', 10)).pack(anchor='w', pady=(0, 10))
        
        # Progress bars frame
        progress_bars_frame = ttk.Frame(progress_frame)
        progress_bars_frame.pack(fill='x', pady=(0, 10))
        
        # Phone lookup progress
        ttk.Label(progress_bars_frame, text="Phone Lookup:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.lookup_progress = ttk.Progressbar(progress_bars_frame, mode='determinate')
        self.lookup_progress.grid(row=0, column=1, sticky='we', padx=(0, 20))
        
        # Image embedding progress
        ttk.Label(progress_bars_frame, text="Image Embedding:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.image_progress = ttk.Progressbar(progress_bars_frame, mode='determinate')
        self.image_progress.grid(row=0, column=3, sticky='we')
        
        progress_bars_frame.columnconfigure(1, weight=1)
        progress_bars_frame.columnconfigure(3, weight=1)
    
    def setup_control_buttons(self, parent):
        """Setup processing control buttons."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', pady=(0, 20))
        
        self.process_btn = ttk.Button(
            control_frame, 
            text="Start Processing", 
            command=self.start_processing,
            state='disabled'
        )
        self.process_btn.pack(side='left', padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            control_frame, 
            text="Stop", 
            command=self.stop_processing,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 5))
        
        self.pause_btn = ttk.Button(
            control_frame, 
            text="Pause", 
            command=self.pause_processing,
            state='disabled'
        )
        self.pause_btn.pack(side='left')
    
    def setup_log_section(self, parent):
        """Setup log display section."""
        log_frame = ttk.LabelFrame(parent, text="Processing Log", padding="10")
        log_frame.pack(fill='both', expand=True)
        
        # Log text area with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(log_container, height=10, wrap='word', font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill='x', pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).pack(side='left')
        ttk.Button(log_controls, text="Export Log", command=self.export_log).pack(side='left', padx=(5, 0))
    
    def check_initial_config(self):
        """Check if initial configuration is needed."""
        if not self.config_manager.is_api_configured():
            self.log_message("Please configure your API key in Settings before processing files.")
            if self.config_manager.get('show_notifications', True):
                messagebox.showinfo(
                    "API Key Required", 
                    "Please configure your Eyecon API key in the Settings dialog before processing files.",
                    icon='info'
                )
    
    def apply_theme(self):
        """Apply the selected theme."""
        theme = self.config_manager.get('theme', 'system')
        # Note: tkinter doesn't have built-in theme switching
        # This would require ttk themes or custom styling
        self.log_message(f"Theme set to: {theme}")
    
    def browse_file(self):
        """Browse for Excel file."""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.file_path_var.set(filename)
            self.validate_file(filename)
    
    def validate_file(self, filename):
        """Validate the selected Excel file."""
        try:
            # Check if file exists
            if not os.path.exists(filename):
                raise FileNotFoundError("File does not exist")
            
            # Check if file is open in Excel (Windows)
            if os.name == 'nt':
                try:
                    os.rename(filename, filename)
                except OSError:
                    raise Exception("File may be open in Excel. Please close it and try again.")
            
            # Check if it's a valid Excel file
            df = pd.read_excel(filename)
            
            # Check for required columns
            if 'Number' not in df.columns:
                raise ValueError("The file must contain a 'Number' column")
            
            # File info
            file_size = os.path.getsize(filename) / 1024  # KB
            file_info = f"Rows: {len(df)} | Size: {file_size:.1f} KB | Valid Excel file"
            
            self.file_info_var.set(f"✅ {file_info}")
            self.process_btn.config(state='normal')
            self.log_message(f"File validated: {filename}")
            
        except Exception as e:
            error_msg = f"Invalid file: {str(e)}"
            self.file_info_var.set(f"❌ {error_msg}")
            self.process_btn.config(state='disabled')
            self.log_message(f"File validation failed: {error_msg}", "error")
            if self.config_manager.get('show_notifications', True):
                messagebox.showerror("File Error", error_msg)
    
    def start_processing(self):
        """Start the complete processing pipeline."""
        if not self.current_file or self.is_processing:
            return
        
        # Validate prerequisites
        if not self.config_manager.is_api_configured():
            messagebox.showerror("Error", "Please configure your API key in Settings first!")
            return
        
        # Check monthly limit
        stats = self.usage_tracker.get_usage_stats()
        monthly_limit = self.config_manager.get('max_requests_per_month', 1000)
        if stats['current_month_usage'] >= monthly_limit:
            response = messagebox.askyesno(
                "Monthly Limit Reached", 
                f"You have reached your monthly limit of {monthly_limit} requests.\n\n"
                f"Would you like to ignore the limit and continue?",
                icon='warning'
            )
            if not response:
                return
        
        # Confirmation dialog
        if self.config_manager.get('show_notifications', True):
            response = messagebox.askyesno(
                "Confirm Processing",
                "Start processing the file? This may take several minutes depending on the file size.",
                icon='question'
            )
            if not response:
                return
        
        # Reset UI state
        self.is_processing = True
        self.stop_requested = False
        self.process_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.pause_btn.config(state='normal')
        self.status_var.set("Starting processing...")
        
        # Reset progress bars
        self.lookup_progress['value'] = 0
        self.image_progress['value'] = 0
        
        # Clear log
        self.clear_log()
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.run_processing_pipeline)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop_processing(self):
        """Stop the processing pipeline."""
        if self.is_processing:
            self.stop_requested = True
            self.phone_lookup.stop()
            self.image_embedder.stop()
            self.status_var.set("Stopping...")
            self.log_message("Processing stopped by user")
            self.stop_btn.config(state='disabled')
    
    def pause_processing(self):
        """Pause/resume processing."""
        # Note: Pause functionality would require additional implementation
        # in the processing modules
        self.log_message("Pause functionality not yet implemented")
    
    def run_processing_pipeline(self):
        """Run the complete processing pipeline in a separate thread."""
        try:
            # Generate output filename
            input_path = Path(self.current_file)
            output_file = input_path.parent / f"{input_path.stem}_processed{input_path.suffix}"
            
            # Step 1: Phone lookup
            if self.stop_requested:
                return
                
            self.update_status("Starting phone number lookup...")
            self.log_message("=== PHONE LOOKUP STARTED ===")
            
            # Configure phone lookup
            self.phone_lookup.configure(
                input_file=str(self.current_file),
                output_file=str(output_file),
                api_key=self.config_manager.get_api_key(),
                api_host=self.config_manager.get('api_host', 'eyecon.p.rapidapi.com'),
                delay=self.config_manager.get('request_delay', 1.5),
                save_interval=self.config_manager.get('save_interval', 10),
                max_retries=self.config_manager.get('max_retries', 3),
                timeout=30,
                log_callback=self.log_message,
                status_callback=self.update_status,
                progress_callback=lambda x: self.update_progress(self.lookup_progress, x),
                usage_callback=self.update_usage_display,
                stop_callback=lambda: self.stop_requested
            )
            
            # Run phone lookup
            lookup_success = self.phone_lookup.run()
            
            if not lookup_success or self.stop_requested:
                self.update_status("Phone lookup stopped or failed")
                return
            
            # Step 2: Image embedding
            if self.stop_requested:
                return
                
            self.update_status("Starting image embedding...")
            self.log_message("=== IMAGE EMBEDDING STARTED ===")
            
            # Configure image embedder
            self.image_embedder.configure(
                input_file=str(output_file),
                output_file=str(output_file),
                max_width=self.config_manager.get('max_image_width', 100),
                max_height=self.config_manager.get('max_image_height', 100),
                image_quality=self.config_manager.get('image_quality', 85),
                row_height=75,
                column_width=15,
                timeout=30,
                enable_cache=True,
                log_callback=self.log_message,
                status_callback=self.update_status,
                progress_callback=lambda x: self.update_progress(self.image_progress, x),
                stop_callback=lambda: self.stop_requested
            )
            
            # Run image embedding
            embed_success = self.image_embedder.run()
            
            # Complete
            if embed_success and not self.stop_requested:
                self.update_status("Processing complete!")
                self.log_message("=== PROCESSING COMPLETE ===")
                self.update_progress(self.image_progress, 100)
                
                # Offer to open output folder
                if self.config_manager.get('auto_open_output', True):
                    self.root.after(0, self.open_output_folder, output_file.parent)
                
                # Show success message
                if self.config_manager.get('show_notifications', True):
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Processing Complete", 
                        f"File processing completed successfully!\n\nOutput file: {output_file.name}"
                    ))
            
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.log_message(error_msg, "error")
            self.update_status("Processing failed with error")
            if self.config_manager.get('show_notifications', True):
                self.root.after(0, lambda: messagebox.showerror("Processing Error", error_msg))
        
        finally:
            self.root.after(0, self.processing_complete)
    
    def processing_complete(self):
        """Clean up after processing completes."""
        self.is_processing = False
        self.process_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.pause_btn.config(state='disabled')
        
        if not hasattr(self, 'processing_thread') or not self.processing_thread.is_alive():
            self.status_var.set("Ready to process")
    
    def open_output_folder(self, folder_path):
        """Open the output folder in file explorer."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS, Linux
                import subprocess
                subprocess.run(['open', folder_path] if sys.platform == 'darwin' 
                             else ['xdg-open', folder_path])
        except Exception as e:
            self.log_message(f"Could not open output folder: {str(e)}", "error")
    
    def show_settings(self):
        """Show the settings dialog."""
        SettingsDialog(self.root, self.config_manager, self.usage_tracker)
    
    def reset_api_counter(self):
        """Reset the API usage counter."""
        if messagebox.askyesno("Confirm Reset", "Reset API usage counter for current month?"):
            self.usage_tracker.reset_current_month()
            self.update_usage_display()
            self.log_message("API usage counter reset")
            messagebox.showinfo("Success", "API counter reset successfully!")
    
    def update_usage_display(self, stats=None):
        """Update the usage counter display."""
        if stats is None:
            stats = self.usage_tracker.get_usage_stats()
        
        self.root.after(0, lambda: self._update_usage_gui(stats))
    
    def _update_usage_gui(self, stats):
        """Update usage GUI elements (called in main thread)."""
        self.current_month_var.set(stats["current_month"])
        self.usage_count_var.set(str(stats["current_month_usage"]))
        self.daily_avg_var.set(str(stats["daily_average"]))
        self.all_time_var.set(str(stats["all_time_usage"]))
        
        # Update monthly limit
        monthly_limit = self.config_manager.get('max_requests_per_month', 1000)
        self.monthly_limit_var.set(str(monthly_limit))
        
        # Update progress bar and color coding
        usage_percentage = (stats["current_month_usage"] / monthly_limit) * 100 if monthly_limit > 0 else 0
        self.usage_progress['value'] = min(usage_percentage, 100)
        
        # Color coding
        if usage_percentage >= 90:
            self.usage_count_label.config(foreground='red')
        elif usage_percentage >= 75:
            self.usage_count_label.config(foreground='orange')
        else:
            self.usage_count_label.config(foreground='blue')
    
    def update_status(self, message):
        """Update status message."""
        self.root.after(0, lambda: self.status_var.set(message))
    
    def update_progress(self, progress_bar, value):
        """Update progress bar."""
        self.root.after(0, lambda: progress_bar.config(value=value))
    
    def log_message(self, message, level="info"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Log to file
        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Send to GUI
        self.root.after(0, self._append_log, log_entry)
    
    def _append_log(self, message):
        """Append message to log (called in main thread)."""
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
    
    def clear_log(self):
        """Clear the log display."""
        self.log_text.delete('1.0', 'end')
    
    def export_log(self):
        """Export log to file."""
        filename = filedialog.asksaveasfilename(
            title="Save Log File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get('1.0', 'end'))
                self.log_message(f"Log exported to: {filename}")
                messagebox.showinfo("Success", "Log exported successfully!")
            except Exception as e:
                self.log_message(f"Error exporting log: {str(e)}", "error")
                messagebox.showerror("Error", f"Could not export log: {str(e)}")


def main():
    """Main application entry point."""
    # Create and run the application
    root = tk.Tk()
    app = PhoneLookupApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()