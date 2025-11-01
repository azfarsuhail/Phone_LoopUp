#!/usr/bin/env python3
"""
Phone Lookup Tool - Main Application
Modern UI with CustomTkinter, ribbon tabs, circular progress, and enhanced dark mode.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import time
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import sys
import logging
import tkinter as tk
from tkinter import ttk

# Add the modules directory to path
sys.path.append(str(Path(__file__).parent))

from modules.phone_lookup import PhoneLookup
from modules.image_embedder import ImageEmbedder
from modules.config_manager import ConfigManager
from modules.usage_tracker import get_usage_tracker
from modules.path_utils import get_logs_path, get_data_path, is_compiled

# Set appearance
ctk.set_appearance_mode("System")  # Default to system theme
ctk.set_default_color_theme("blue")  # Default color theme

class SplashScreen:
    """Splash screen shown during application startup."""
    
    def __init__(self):
        self.splash = ctk.CTkToplevel()
        self.splash.title("Phone Lookup Tool")
        self.splash.geometry("400x200")
        self.splash.overrideredirect(True)
        
        # Center the splash screen
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() - 400) // 2
        y = (self.splash.winfo_screenheight() - 200) // 2
        self.splash.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup splash screen UI."""
        # Main frame
        main_frame = ctk.CTkFrame(self.splash, fg_color="transparent")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # App icon/logo (placeholder)
        ctk.CTkLabel(main_frame, text="📱", font=ctk.CTkFont(size=48)).pack(pady=10)
        
        # App title
        ctk.CTkLabel(main_frame, text="Phone Lookup Tool", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack(pady=5)
        
        # Version/subtitle
        ctk.CTkLabel(main_frame, text="Professional Phone Number Analysis",
                    font=ctk.CTkFont(size=12)).pack(pady=5)
        
        # Loading progress
        self.progress = ctk.CTkProgressBar(main_frame, width=300, height=20)
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        # Loading label
        self.loading_label = ctk.CTkLabel(main_frame, text="Loading...")
        self.loading_label.pack()
        
    def update_progress(self, value, text="Loading..."):
        """Update splash screen progress."""
        self.progress.set(value)
        self.loading_label.configure(text=text)
        self.splash.update()
        
    def close(self):
        """Close the splash screen."""
        self.splash.destroy()

class ModernProgressFrame(ctk.CTkFrame):
    """Modern circular progress indicator frame."""
    
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.title = title
        self.progress_value = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Setup circular progress UI."""
        # Title
        ctk.CTkLabel(self, text=self.title, font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        # Circular progress container
        progress_container = ctk.CTkFrame(self, fg_color="transparent", width=120, height=120)
        progress_container.pack(pady=10)
        progress_container.pack_propagate(False)
        
        # Progress circle (simulated with progress bar in circle shape)
        self.progress_bar = ctk.CTkProgressBar(progress_container, width=100, height=100, 
                                              progress_color="green", fg_color="gray")
        self.progress_bar.place(relx=0.5, rely=0.5, anchor="center")
        self.progress_bar.set(0)
        
        # Percentage text
        self.percentage_label = ctk.CTkLabel(progress_container, text="0%", 
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.percentage_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Status text
        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)
        
    def update_progress(self, value, status="Processing"):
        """Update progress value and status."""
        self.progress_value = value
        self.progress_bar.set(value / 100)
        self.percentage_label.configure(text=f"{int(value)}%")
        self.status_label.configure(text=status)

class SettingsDialog:
    """Modern settings dialog with category tabs."""
    
    def __init__(self, parent, config_manager, usage_tracker):
        self.parent = parent
        self.config_manager = config_manager
        self.usage_tracker = usage_tracker
        self.dialog = None
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the settings dialog window."""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("700x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        
        # Make non-modal
        self.dialog.grab_set()
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        """Create settings dialog widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        ctk.CTkLabel(main_frame, text="Application Settings", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        # Tab view
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.api_tab = self.tabview.add("API Settings")
        self.processing_tab = self.tabview.add("Processing")
        self.image_tab = self.tabview.add("Images")
        self.ui_tab = self.tabview.add("UI/Appearance")
        
        # Setup each tab
        self.create_api_tab()
        self.create_processing_tab()
        self.create_image_tab()
        self.create_ui_tab()
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Save", command=self.save_settings,
                     width=100).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Cancel", command=self.dialog.destroy,
                     width=100, fg_color="gray").pack(side='right')
        ctk.CTkButton(button_frame, text="Reset to Defaults", 
                     command=self.reset_to_defaults, width=120).pack(side='left')
        ctk.CTkButton(button_frame, text="Reset Usage Counter", 
                     command=self.reset_usage_counter, width=140).pack(side='left', padx=(0, 10))
    
    def create_api_tab(self):
        """Create API settings tab."""
        # API Key
        ctk.CTkLabel(self.api_tab, text="API Key:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky='w', pady=10)
        self.api_key_var = ctk.StringVar()
        api_entry = ctk.CTkEntry(self.api_tab, textvariable=self.api_key_var, width=400, show="•")
        api_entry.grid(row=0, column=1, sticky='we', pady=10, padx=(10, 0))
        
        # API Host
        ctk.CTkLabel(self.api_tab, text="API Host:").grid(row=1, column=0, sticky='w', pady=8)
        self.api_host_var = ctk.StringVar()
        ctk.CTkEntry(self.api_tab, textvariable=self.api_host_var, width=400).grid(row=1, column=1, sticky='we', pady=8, padx=(10, 0))
        
        # Monthly Limit
        ctk.CTkLabel(self.api_tab, text="Monthly API Limit:").grid(row=2, column=0, sticky='w', pady=8)
        self.monthly_limit_var = ctk.IntVar()
        ctk.CTkEntry(self.api_tab, textvariable=self.monthly_limit_var, width=150).grid(row=2, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # Current Usage
        ctk.CTkLabel(self.api_tab, text="Current Month Usage:").grid(row=3, column=0, sticky='w', pady=8)
        self.current_usage_var = ctk.StringVar(value="0")
        usage_frame = ctk.CTkFrame(self.api_tab, fg_color="transparent")
        usage_frame.grid(row=3, column=1, sticky='w', pady=8, padx=(10, 0))
        ctk.CTkEntry(usage_frame, textvariable=self.current_usage_var, width=100, state='readonly').pack(side='left')
        ctk.CTkButton(usage_frame, text="Edit", width=60, command=self.edit_usage_counter).pack(side='left', padx=(5, 0))
        
        self.api_tab.columnconfigure(1, weight=1)
    
    def create_processing_tab(self):
        """Create processing settings tab."""
        # Request Delay
        ctk.CTkLabel(self.processing_tab, text="Request Delay (seconds):").grid(row=0, column=0, sticky='w', pady=10)
        self.delay_var = ctk.DoubleVar()
        ctk.CTkEntry(self.processing_tab, textvariable=self.delay_var, width=150).grid(row=0, column=1, sticky='w', pady=10, padx=(10, 0))
        
        # Save Interval
        ctk.CTkLabel(self.processing_tab, text="Save Interval:").grid(row=1, column=0, sticky='w', pady=8)
        self.save_interval_var = ctk.IntVar()
        ctk.CTkEntry(self.processing_tab, textvariable=self.save_interval_var, width=150).grid(row=1, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # Max Retries
        ctk.CTkLabel(self.processing_tab, text="Max Retries:").grid(row=2, column=0, sticky='w', pady=8)
        self.max_retries_var = ctk.IntVar()
        ctk.CTkEntry(self.processing_tab, textvariable=self.max_retries_var, width=150).grid(row=2, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # Default Country Code
        ctk.CTkLabel(self.processing_tab, text="Default Country Code:").grid(row=3, column=0, sticky='w', pady=8)
        self.country_code_var = ctk.StringVar()
        ctk.CTkEntry(self.processing_tab, textvariable=self.country_code_var, width=100).grid(row=3, column=1, sticky='w', pady=8, padx=(10, 0))
        
        self.processing_tab.columnconfigure(1, weight=1)
    
    def create_image_tab(self):
        """Create image settings tab."""
        # Max Width
        ctk.CTkLabel(self.image_tab, text="Max Image Width (pixels):").grid(row=0, column=0, sticky='w', pady=10)
        self.max_width_var = ctk.IntVar()
        ctk.CTkEntry(self.image_tab, textvariable=self.max_width_var, width=150).grid(row=0, column=1, sticky='w', pady=10, padx=(10, 0))
        
        # Max Height
        ctk.CTkLabel(self.image_tab, text="Max Image Height (pixels):").grid(row=1, column=0, sticky='w', pady=8)
        self.max_height_var = ctk.IntVar()
        ctk.CTkEntry(self.image_tab, textvariable=self.max_height_var, width=150).grid(row=1, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # Image Quality
        ctk.CTkLabel(self.image_tab, text="Image Quality (%):").grid(row=2, column=0, sticky='w', pady=8)
        self.image_quality_var = ctk.IntVar()
        ctk.CTkEntry(self.image_tab, textvariable=self.image_quality_var, width=150).grid(row=2, column=1, sticky='w', pady=8, padx=(10, 0))
        
        self.image_tab.columnconfigure(1, weight=1)
    
    def create_ui_tab(self):
        """Create UI settings tab."""
        # Theme
        ctk.CTkLabel(self.ui_tab, text="Theme:").grid(row=0, column=0, sticky='w', pady=10)
        self.theme_var = ctk.StringVar()
        theme_combo = ctk.CTkComboBox(self.ui_tab, values=["System", "Light", "Dark"], 
                                    variable=self.theme_var, width=150)
        theme_combo.grid(row=0, column=1, sticky='w', pady=10, padx=(10, 0))
        
        # Color Theme
        ctk.CTkLabel(self.ui_tab, text="Color Theme:").grid(row=1, column=0, sticky='w', pady=8)
        self.color_theme_var = ctk.StringVar()
        color_combo = ctk.CTkComboBox(self.ui_tab, 
                                    values=["blue", "green", "dark-blue", "purple"], 
                                    variable=self.color_theme_var, width=150)
        color_combo.grid(row=1, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # High Contrast
        self.high_contrast_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self.ui_tab, text="High Contrast Mode", variable=self.high_contrast_var).grid(row=2, column=0, columnspan=2, sticky='w', pady=8)
        
        # Notifications
        self.show_notifications_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self.ui_tab, text="Show Notifications", variable=self.show_notifications_var).grid(row=3, column=0, columnspan=2, sticky='w', pady=8)
        
        # Auto-open output
        self.auto_open_output_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self.ui_tab, text="Auto-open Output Folder", variable=self.auto_open_output_var).grid(row=4, column=0, columnspan=2, sticky='w', pady=8)
        
        self.ui_tab.columnconfigure(1, weight=1)
    
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
        self.theme_var.set(self.config_manager.get('theme', 'System').title())
        self.color_theme_var.set(self.config_manager.get('color_theme', 'blue'))
        self.high_contrast_var.set(self.config_manager.get('high_contrast', False))
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
        self.config_manager.set('theme', self.theme_var.get().lower())
        self.config_manager.set('color_theme', self.color_theme_var.get())
        self.config_manager.set('high_contrast', self.high_contrast_var.get())
        self.config_manager.set('show_notifications', self.show_notifications_var.get())
        self.config_manager.set('auto_open_output', self.auto_open_output_var.get())
        
        # Apply theme immediately
        self.parent.apply_theme()
        
        messagebox.showinfo("Success", "Settings saved successfully!", parent=self.dialog)
    
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
        new_value = ctk.CTkInputDialog(
            text="Enter new usage count:", 
            title="Edit Usage Counter"
        ).get_input()
        
        if new_value is not None and new_value.isdigit():
            # This would require modifying the usage tracker to set absolute values
            messagebox.showinfo("Info", "Manual usage editing requires code modification.", parent=self.dialog)

class PhoneLookupApp:
    """Main application class with modern UI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Number Lookup Tool")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # Show splash screen
        self.splash = SplashScreen()
        self.root.after(100, self.initialize_app)
    
    def initialize_app(self):
        """Initialize application components after splash screen."""
        try:
            self.splash.update_progress(10, "Loading configuration...")
            
            # Initialize components
            self.config_manager = ConfigManager()
            self.usage_tracker = get_usage_tracker()
            self.phone_lookup = PhoneLookup()
            self.image_embedder = ImageEmbedder()
            
            self.splash.update_progress(30, "Setting up UI...")
            
            # State variables
            self.current_file = None
            self.is_processing = False
            self.processing_thread = None
            self.stop_requested = False
            
            # Setup logging
            self.setup_logging()
            
            # Configure CustomTkinter
            self.setup_ctk()
            
            self.splash.update_progress(60, "Creating interface...")
            
            # Create UI
            self.setup_ui()
            
            # Apply theme
            self.apply_theme()
            
            self.splash.update_progress(80, "Finalizing...")
            
            # Check initial configuration
            self.check_initial_config()
            
            # Update usage display
            self.update_usage_display()
            # In the __init__ method, add these at the end:
            self.setup_keyboard_shortcuts()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.splash.update_progress(100, "Ready!")
            self.root.after(500, self.splash.close)
            
        except Exception as e:
            self.splash.close()
            messagebox.showerror("Initialization Error", f"Failed to initialize application: {str(e)}")
            self.root.destroy()
    
    def setup_ctk(self):
        """Setup CustomTkinter configuration."""
        # Set theme based on config
        theme = self.config_manager.get('theme', 'system').lower()
        color_theme = self.config_manager.get('color_theme', 'blue')
        
        ctk.set_appearance_mode(theme.title())
        ctk.set_default_color_theme(color_theme)
    
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
        """Setup the main user interface with ribbon tabs and modern design."""
        # Create main container
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create ribbon-style menu
        self.setup_ribbon_menu()
        
        # Create scrollable main content
        self.setup_scrollable_content()
    
    def setup_ribbon_menu(self):
        """Setup ribbon-style menu bar."""
        ribbon_frame = ctk.CTkFrame(self.main_frame, height=80)
        ribbon_frame.pack(fill='x', pady=(0, 10))
        ribbon_frame.pack_propagate(False)
        
        # File section
        file_section = ctk.CTkFrame(ribbon_frame, fg_color="transparent")
        file_section.pack(side='left', padx=20, pady=10)
        
        ctk.CTkLabel(file_section, text="File", font=ctk.CTkFont(weight="bold")).pack()
        ctk.CTkButton(file_section, text="📁 Open", width=80, 
                     command=self.browse_file).pack(pady=5)
        
        # Process section
        process_section = ctk.CTkFrame(ribbon_frame, fg_color="transparent")
        process_section.pack(side='left', padx=20, pady=10)
        
        ctk.CTkLabel(process_section, text="Process", font=ctk.CTkFont(weight="bold")).pack()
        self.process_btn = ctk.CTkButton(process_section, text="▶ Start", width=80,
                                       command=self.start_processing, state='disabled')
        self.process_btn.pack(pady=5)
        
        # Control section
        control_section = ctk.CTkFrame(ribbon_frame, fg_color="transparent")
        control_section.pack(side='left', padx=20, pady=10)
        
        ctk.CTkLabel(control_section, text="Controls", font=ctk.CTkFont(weight="bold")).pack()
        control_buttons = ctk.CTkFrame(control_section, fg_color="transparent")
        control_buttons.pack(pady=5)
        
        self.stop_btn = ctk.CTkButton(control_buttons, text="⏹ Stop", width=60,
                                    command=self.stop_processing, state='disabled',
                                    fg_color="#d9534f", hover_color="#c9302c")
        self.stop_btn.pack(side='left', padx=2)
        
        self.pause_btn = ctk.CTkButton(control_buttons, text="⏸ Pause", width=60,
                                     command=self.pause_processing, state='disabled')
        self.pause_btn.pack(side='left', padx=2)
        
        # Settings section
        settings_section = ctk.CTkFrame(ribbon_frame, fg_color="transparent")
        settings_section.pack(side='right', padx=20, pady=10)
        
        ctk.CTkLabel(settings_section, text="Settings", font=ctk.CTkFont(weight="bold")).pack()
        ctk.CTkButton(settings_section, text="⚙ Settings", width=80,
                     command=self.show_settings).pack(pady=5)
        
        # Theme toggle
        theme_section = ctk.CTkFrame(ribbon_frame, fg_color="transparent")
        theme_section.pack(side='right', padx=20, pady=10)
        
        ctk.CTkLabel(theme_section, text="Theme", font=ctk.CTkFont(weight="bold")).pack()
        self.theme_btn = ctk.CTkButton(theme_section, text="🌙 Dark", width=80,
                                     command=self.toggle_theme)
        self.theme_btn.pack(pady=5)
    
    def setup_scrollable_content(self):
        """Setup scrollable main content area."""
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scrollable_frame.pack(fill='both', expand=True)
        
        # API Usage Stats Card
        self.setup_usage_card()
        
        # File Upload Card
        self.setup_file_upload_card()
        
        # Progress Cards
        self.setup_progress_cards()
        
        # Log Card
        self.setup_log_card()
    
    def setup_usage_card(self):
        """Setup API usage statistics card."""
        usage_card = ctk.CTkFrame(self.scrollable_frame)
        usage_card.pack(fill='x', pady=(0, 15))
        
        # Card header
        header = ctk.CTkFrame(usage_card, fg_color="transparent")
        header.pack(fill='x', padx=15, pady=10)
        ctk.CTkLabel(header, text="📊 API Usage Statistics", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side='left')
        
        # Stats grid
        stats_grid = ctk.CTkFrame(usage_card, fg_color="transparent")
        stats_grid.pack(fill='x', padx=15, pady=(0, 10))
        
        # Row 1
        ctk.CTkLabel(stats_grid, text="Current Month:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.current_month_var = ctk.StringVar(value="2024-01")
        ctk.CTkLabel(stats_grid, textvariable=self.current_month_var).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        ctk.CTkLabel(stats_grid, text="All time total:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.all_time_var = ctk.StringVar(value="0")
        ctk.CTkLabel(stats_grid, textvariable=self.all_time_var).grid(row=0, column=3, sticky='w', padx=5, pady=5)
        
        # Row 2
        ctk.CTkLabel(stats_grid, text="Requests this month:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.usage_count_var = ctk.StringVar(value="0")
        self.usage_count_label = ctk.CTkLabel(stats_grid, textvariable=self.usage_count_var, 
                                             font=ctk.CTkFont(size=14, weight="bold"))
        self.usage_count_label.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ctk.CTkLabel(stats_grid, text="Monthly Limit:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.monthly_limit_var = ctk.StringVar(value="1000")
        ctk.CTkLabel(stats_grid, textvariable=self.monthly_limit_var).grid(row=1, column=3, sticky='w', padx=5, pady=5)
        
        # Row 3
        ctk.CTkLabel(stats_grid, text="Daily average:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.daily_avg_var = ctk.StringVar(value="0.0")
        ctk.CTkLabel(stats_grid, textvariable=self.daily_avg_var).grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # Usage progress bar
        self.usage_progress = ctk.CTkProgressBar(usage_card, height=20)
        self.usage_progress.pack(fill='x', padx=15, pady=(0, 10))
        self.usage_progress.set(0)
        
        # Configure grid weights
        for i in range(4):
            stats_grid.columnconfigure(i, weight=1)
    
    def setup_file_upload_card(self):
        """Setup file upload card with drag & drop support."""
        upload_card = ctk.CTkFrame(self.scrollable_frame)
        upload_card.pack(fill='x', pady=(0, 15))
        
        # Card header
        header = ctk.CTkFrame(upload_card, fg_color="transparent")
        header.pack(fill='x', padx=15, pady=10)
        ctk.CTkLabel(header, text="📁 File Upload", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side='left')
        
        # File selection
        file_select_frame = ctk.CTkFrame(upload_card, fg_color="transparent")
        file_select_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        ctk.CTkLabel(file_select_frame, text="Select Excel File:").pack(side='left', padx=(0, 10))
        self.file_path_var = ctk.StringVar()
        file_entry = ctk.CTkEntry(file_select_frame, textvariable=self.file_path_var, width=400)
        file_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ctk.CTkButton(file_select_frame, text="Browse", command=self.browse_file).pack(side='left')
        
        # Drag & drop area
        drop_frame = ctk.CTkFrame(upload_card, height=80, border_width=2, border_color="gray")
        drop_frame.pack(fill='x', padx=15, pady=(0, 10))
        drop_frame.pack_propagate(False)
        
        ctk.CTkLabel(drop_frame, text="📎 Drag & Drop Excel file here", 
                    text_color="gray", font=ctk.CTkFont(size=12)).pack(expand=True)
        
        # File info
        self.file_info_var = ctk.StringVar(value="No file selected")
        ctk.CTkLabel(upload_card, textvariable=self.file_info_var, 
                    text_color="gray").pack(anchor='w', padx=15, pady=(0, 10))
        
        # Bind drag & drop events
        drop_frame.bind("<Button-1>", lambda e: self.browse_file())
        file_entry.bind("<Button-1>", lambda e: self.browse_file())
    
    def setup_progress_cards(self):
        """Setup progress tracking cards with circular indicators."""
        progress_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        progress_container.pack(fill='x', pady=(0, 15))
        
        # Status
        self.status_var = ctk.StringVar(value="Ready to process")
        status_label = ctk.CTkLabel(progress_container, textvariable=self.status_var, 
                                   font=ctk.CTkFont(size=12, weight="bold"))
        status_label.pack(anchor='w', pady=(0, 10))
        
        # Progress cards side by side
        progress_cards_frame = ctk.CTkFrame(progress_container, fg_color="transparent")
        progress_cards_frame.pack(fill='x')
        
        # Phone lookup progress card
        self.lookup_progress_card = ModernProgressFrame(progress_cards_frame, "Phone Lookup")
        self.lookup_progress_card.pack(side='left', padx=(0, 10), fill='both', expand=True)
        
        # Image embedding progress card
        self.image_progress_card = ModernProgressFrame(progress_cards_frame, "Image Embedding")
        self.image_progress_card.pack(side='left', fill='both', expand=True)
    
    def setup_log_card(self):
        """Setup log display card with proper scrolling."""
        log_card = ctk.CTkFrame(self.scrollable_frame)
        log_card.pack(fill='both', expand=True)
        
        # Card header with controls
        header = ctk.CTkFrame(log_card, fg_color="transparent")
        header.pack(fill='x', padx=15, pady=10)
        
        ctk.CTkLabel(header, text="📋 Processing Log", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side='left')
        
        # Log controls
        log_controls = ctk.CTkFrame(header, fg_color="transparent")
        log_controls.pack(side='right')
        
        ctk.CTkButton(log_controls, text="📥 Export", width=80,
                     command=self.export_log).pack(side='left', padx=(0, 5))
        ctk.CTkButton(log_controls, text="🗑️ Clear", width=80,
                     command=self.clear_log).pack(side='left')
        
        # Log text area with proper scrolling
        log_container = ctk.CTkFrame(log_card)
        log_container.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Use tkinter Text widget for colored logs with CustomTkinter styling
        self.log_text = tk.Text(log_container, wrap='word', font=('Consolas', 10),
                               bg='#2b2b2b', fg='white', insertbackground='white',
                               relief='flat', padx=10, pady=10)
        
        # Configure tags for colored text
        self.log_text.tag_configure("error", foreground="#ff4444")
        self.log_text.tag_configure("warning", foreground="#ffaa00")
        self.log_text.tag_configure("info", foreground="#ffffff")
        self.log_text.tag_configure("success", foreground="#2ecc71")
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(log_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current = ctk.get_appearance_mode()
        new_theme = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        self.theme_btn.configure(text="🌙 Dark" if new_theme == "Dark" else "☀️ Light")
        self.config_manager.set('theme', new_theme.lower())
    
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
            self.process_btn.configure(state='normal')
            self.log_message(f"File validated: {filename}")
            
        except Exception as e:
            error_msg = f"Invalid file: {str(e)}"
            self.file_info_var.set(f"❌ {error_msg}")
            self.process_btn.configure(state='disabled')
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
        self.process_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.pause_btn.configure(state='normal')
        self.status_var.set("Starting processing...")
        
        # Reset progress indicators
        self.lookup_progress_card.update_progress(0, "Ready")
        self.image_progress_card.update_progress(0, "Ready")
        
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
            self.log_message("Processing stopped by user", "warning")
            self.stop_btn.configure(state='disabled')

    def pause_processing(self):
        """Pause/resume processing."""
        # Note: Pause functionality would require additional implementation
        # in the processing modules
        self.log_message("Pause functionality not yet implemented", "warning")

    def run_processing_pipeline(self):
        """Run the complete processing pipeline in a separate thread."""
        try:
            # Generate output filename
            input_path = Path(self.current_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = input_path.parent / f"{input_path.stem}_processed_{timestamp}{input_path.suffix}"
            
            # Step 1: Phone lookup
            if self.stop_requested:
                return
                
            self.update_status("Starting phone number lookup...")
            self.log_message("=== PHONE LOOKUP STARTED ===", "info")

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
                progress_callback=self.update_lookup_progress,
                usage_callback=self.update_usage_display,
                stop_callback=lambda: self.stop_requested
            )
            
            # Run phone lookup
            lookup_success = self.phone_lookup.run()
            
            if not lookup_success or self.stop_requested:
                self.update_status("Phone lookup stopped or failed")
                if not lookup_success:
                    self.log_message("Phone lookup failed", "error")
                return
            
            # Step 2: Image embedding
            if self.stop_requested:
                return
                
            self.update_status("Starting image embedding...")
            self.log_message("=== IMAGE EMBEDDING STARTED ===", "info")

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
                progress_callback=self.update_image_progress,
                stop_callback=lambda: self.stop_requested
            )
            
            # Run image embedding
            embed_success = self.image_embedder.run()
            
            # Complete
            if embed_success and not self.stop_requested:
                self.update_status("Processing complete!")
                self.log_message("=== PROCESSING COMPLETE ===", "success")
                self.update_image_progress(100, "Complete")
                
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

    def update_lookup_progress(self, value):
        """Update phone lookup progress with circular indicator."""
        status = "Processing"
        if value >= 100:
            status = "Complete"
        elif value <= 0:
            status = "Ready"
        
        self.root.after(0, lambda: self.lookup_progress_card.update_progress(value, status))

    def update_image_progress(self, value):
        """Update image embedding progress with circular indicator."""
        status = "Processing"
        if value >= 100:
            status = "Complete"
        elif value <= 0:
            status = "Ready"
        
        self.root.after(0, lambda: self.image_progress_card.update_progress(value, status))

    def processing_complete(self):
        """Clean up after processing completes."""
        self.is_processing = False
        self.process_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.pause_btn.configure(state='disabled')
        
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
            self.log_message(f"Opened output folder: {folder_path}", "info")
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
            self.log_message("API usage counter reset", "info")
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
        self.daily_avg_var.set(f"{stats['daily_average']:.1f}")
        self.all_time_var.set(str(stats["all_time_usage"]))
        
        # Update monthly limit
        monthly_limit = self.config_manager.get('max_requests_per_month', 1000)
        self.monthly_limit_var.set(str(monthly_limit))
        
        # Update progress bar and color coding
        usage_percentage = (stats["current_month_usage"] / monthly_limit) if monthly_limit > 0 else 0
        self.usage_progress.set(min(usage_percentage, 1.0))
        
        # Color coding for usage count
        if usage_percentage >= 0.9:
            self.usage_count_label.configure(text_color="#ff4444")  # red
            self.usage_progress.configure(progress_color="#ff4444")
        elif usage_percentage >= 0.75:
            self.usage_count_label.configure(text_color="#ffaa00")  # orange
            self.usage_progress.configure(progress_color="#ffaa00")
        else:
            self.usage_count_label.configure(text_color="#2ecc71")  # green
            self.usage_progress.configure(progress_color="#2ecc71")

    def update_status(self, message):
        """Update status message."""
        self.root.after(0, lambda: self.status_var.set(message))

    def log_message(self, message, level="info"):
        """Log message with timestamp and colored text."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine tag and prefix based on level
        if level == "error":
            tag = "error"
            prefix = "❌ ERROR:"
            log_level = "ERROR"
        elif level == "warning":
            tag = "warning"
            prefix = "⚠️ WARN:"
            log_level = "WARNING"
        elif level == "success":
            tag = "success"
            prefix = "✅ SUCCESS:"
            log_level = "INFO"
        else:
            tag = "info"
            prefix = "ℹ️ INFO:"
            log_level = "INFO"
        
        log_entry = f"[{timestamp}] {prefix} {message}"
        
        # Log to file
        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Send to GUI with colored text
        self.root.after(0, self._append_log, log_entry, tag)

    def _append_log(self, message, tag):
        """Append message to log with colored text (called in main thread)."""
        self.log_text.insert('end', message + '\n', tag)
        self.log_text.see('end')  # Auto-scroll to bottom
        self.log_text.update()

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
                # Get all text without tags for export
                log_content = self.log_text.get('1.0', 'end')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.log_message(f"Log exported to: {filename}", "success")
                messagebox.showinfo("Success", "Log exported successfully!")
            except Exception as e:
                self.log_message(f"Error exporting log: {str(e)}", "error")
                messagebox.showerror("Error", f"Could not export log: {str(e)}")

    def apply_theme(self):
        """Apply the selected theme."""
        theme = self.config_manager.get('theme', 'system').lower()
        color_theme = self.config_manager.get('color_theme', 'blue')
        high_contrast = self.config_manager.get('high_contrast', False)
        
        ctk.set_appearance_mode(theme.title())
        ctk.set_default_color_theme(color_theme)
        
        # Update theme button text
        current_theme = ctk.get_appearance_mode()
        self.theme_btn.configure(text="🌙 Dark" if current_theme == "Dark" else "☀️ Light")
        
        # Apply high contrast if enabled
        if high_contrast:
            self._apply_high_contrast()
        
        self.log_message(f"Theme applied: {theme} with {color_theme} color scheme", "info")

    def _apply_high_contrast(self):
        """Apply high contrast styling."""
        # This would modify specific colors for better visibility
        # For now, we'll just log it
        self.log_message("High contrast mode enabled", "info")

    def check_initial_config(self):
        """Check if initial configuration is needed."""
        if not self.config_manager.is_api_configured():
            self.log_message("Please configure your API key in Settings before processing files.", "warning")
            if self.config_manager.get('show_notifications', True):
                messagebox.showinfo(
                    "API Key Required", 
                    "Please configure your Eyecon API key in the Settings dialog before processing files.",
                    icon='info'
                )

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        # File operations
        self.root.bind('<Control-o>', lambda e: self.browse_file())
        self.root.bind('<Control-O>', lambda e: self.browse_file())
        
        # Settings
        self.root.bind('<Control-s>', lambda e: self.show_settings())
        self.root.bind('<Control-S>', lambda e: self.show_settings())
        
        # Processing
        self.root.bind('<F5>', lambda e: self.start_processing() if not self.is_processing else None)
        self.root.bind('<Control-p>', lambda e: self.start_processing() if not self.is_processing else None)
        self.root.bind('<Control-P>', lambda e: self.start_processing() if not self.is_processing else None)
        
        # Stop processing
        self.root.bind('<Escape>', lambda e: self.stop_processing() if self.is_processing else None)
        
        # Quit
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-Q>', lambda e: self.root.quit())

    def on_closing(self):
        """Handle application closing."""
        if self.is_processing:
            if messagebox.askyesno("Confirm Exit", 
                                 "Processing is still running. Are you sure you want to exit?"):
                self.stop_processing()
                self.root.quit()
        else:
            self.root.quit()


def main():
    """Main application entry point."""
    # Create and run the application
    root = ctk.CTk()
    app = PhoneLookupApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()