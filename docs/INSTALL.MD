# Installation Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
   - [Method 1: From Source (Recommended)](#method-1-from-source-recommended)
   - [Method 2: Using PyInstaller Executable](#method-2-using-pyinstaller-executable)
   - [Method 3: Using pip](#method-3-using-pip)
3. [Platform-Specific Instructions](#platform-specific-instructions)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Operating System**: Windows 7+, macOS 10.12+, or Linux (Ubuntu 16.04+, CentOS 7+)
- **Python**: Version 3.8 or higher
- **Disk Space**: At least 100 MB free space
- **Memory**: Minimum 2 GB RAM (4 GB recommended)

### Required Accounts
- **Eyecon API Account**: Get your API key from [RapidAPI Eyecon](https://rapidapi.com/eyecon/api/eyecon)

## Installation Methods

### Method 1: From Source (Recommended)

#### Step 1: Download the Source Code
```bash
# Clone the repository
git clone https://https://github.com/azfarsuhail/Phone_LoopUp.git
cd Phone_LoopUp

# Or download and extract the ZIP file
# Then navigate to the extracted directory
```

#### Step 2: Create a Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Run the Application
```bash
python main.py
```

### Method 2: Using PyInstaller Executable

#### For End Users (No Python Required)

1. **Download the latest release** from the GitHub releases page
2. **Extract the ZIP file** to your desired location
3. **Run the executable**:
   - Windows: Double-click `PhoneLookupTool.exe`
   - macOS: Double-click `PhoneLookupTool.app`
   - Linux: Run `./PhoneLookupTool` from terminal

#### For Developers (Building from Source)

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**:
   ```bash
   pyinstaller build.spec
   ```

3. **Find the executable** in the `dist/` folder

### Method 3: Using pip

#### Installation
```bash
pip install phone-lookup-tool
```

#### Running
```bash
phone-lookup-tool
```

## Platform-Specific Instructions

### Windows

#### Additional Requirements
- Microsoft Visual C++ Redistributable (usually already installed)

#### Installation Steps
1. Download the Windows executable from releases
2. Right-click → "Run as administrator" (if needed)
3. The application will create necessary folders in `%LOCALAPPDATA%`

#### Troubleshooting
- If you get security warnings, click "More info" → "Run anyway"
- For permission errors, run as administrator

### macOS

#### Additional Requirements
- macOS 10.12 or later

#### Installation Steps
1. Download the macOS .dmg file from releases
2. Drag the application to Applications folder
3. Right-click → "Open" if you get security warnings

#### Troubleshooting
- If blocked by Gatekeeper:
  - Right-click → "Open"
  - Or go to System Preferences → Security & Privacy → Allow

### Linux

#### Additional Requirements
- GTK+ 3.0 or higher
- libnotify for notifications

#### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-tk python3-pil.imagetk

# Then follow Method 1 or use the provided AppImage
```

#### CentOS/RHEL/Fedora
```bash
# Install system dependencies
sudo yum install tkinter PIL
# or for newer versions:
sudo dnf install python3-tkinter python3-pillow
```

#### Installation Steps
1. Download the AppImage from releases
2. Make it executable: `chmod +x PhoneLookupTool.AppImage`
3. Run: `./PhoneLookupTool.AppImage`

## Verification

### Step 1: First Launch
1. Start the application
2. You should see the main window with API usage statistics
3. Check that all menus are accessible

### Step 2: Configuration
1. Go to Settings → API Settings
2. Enter your Eyecon API key
3. Save the configuration

### Step 3: Test with Sample Data
1. Create a test Excel file with a 'Number' column
2. Add a few test phone numbers
3. Process the file to verify everything works

## Troubleshooting

### Common Installation Issues

#### Python Not Found
```bash
# Check Python installation
python --version
# or
python3 --version

# If not found, download from python.org
```

#### Permission Errors
```bash
# On Linux/macOS, you might need:
chmod +x PhoneLookupTool

# On Windows, run as administrator
```

#### Missing Dependencies
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

#### Application Won't Start
1. Check the logs in the application data directory
2. Verify Python version compatibility
3. Check system requirements

### Getting Help

If you encounter issues:

1. **Check the logs** in the application data directory
2. **Verify your API key** is correct and active
3. **Check the GitHub issues** for similar problems
4. **Contact support** with:
   - Your operating system and version
   - Python version
   - Error messages from logs
   - Steps to reproduce the issue

## Updating

### From Source
```bash
git pull
pip install --upgrade -r requirements.txt
```

### Executable
Download the latest release and replace the old executable.

### pip
```bash
pip install --upgrade phone-lookup-tool
```

## Uninstallation

### From Source
```bash
# Delete the project directory
rm -rf PhoneLookupTool

# Remove virtual environment (if used)
rm -rf venv
```

### Executable
Delete the executable file and application data directory:
- Windows: `%LOCALAPPDATA%\PhoneLookupTool\`
- macOS: `~/Library/Application Support/PhoneLookupTool/`
- Linux: `~/.local/share/PhoneLookupTool/`

### pip
```bash
pip uninstall phone-lookup-tool
