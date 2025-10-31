# User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface Overview](#user-interface-overview)
3. [Configuration](#configuration)
4. [Processing Files](#processing-files)
5. [API Usage Management](#api-usage-management)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Getting Started

### First Time Setup

1. **Launch the Application**
   - Double-click the executable or run `python main.py`

2. **Configure API Settings**
   - Click "Settings" → "Configuration"
   - Enter your Eyecon API key
   - Configure other settings as needed
   - Click "Save"

3. **Prepare Your Data**
   - Create an Excel file with a 'Number' column
   - Add phone numbers you want to lookup

### Input File Requirements

Your Excel file must contain:
- A column named **'Number'** with phone numbers
- Supported formats: `.xlsx`, `.xls`

#### Example Input File:
| Number       | Name     | Other Data |
|-------------|----------|------------|
| 923001234567 | John Doe | ...        |
| 03001234567  | Jane Smith | ...       |

#### Supported Phone Number Formats:
- `923001234567` (International)
- `03001234567` (Local with 0)
- `+923001234567` (International with +)

## User Interface Overview

### Main Window Components

1. **API Usage Statistics**
   - Current month usage
   - Daily average
   - All-time total
   - Usage trends

2. **File Upload Section**
   - Browse for Excel files
   - File validation and info
   - Start processing button

3. **Progress Tracking**
   - Overall progress bar
   - Current operation progress
   - Status messages

4. **Processing Log**
   - Real-time operation logs
   - Error messages
   - Success notifications

### Menu Options

#### File Menu
- **Open File**: Select input Excel file
- **Exit**: Close the application

#### Settings Menu
- **Configuration**: Modify application settings
- **Reset API Counter**: Reset current month usage

## Configuration

### API Settings Tab

#### Required Settings
- **API Key**: Your Eyecon API key from RapidAPI
- **API Host**: Usually `eyecon.p.rapidapi.com`

#### Optional Settings
- **Request Delay**: Seconds between API calls (1.5 recommended)
- **Save Interval**: Rows processed between auto-saves
- **Max Requests/Minute**: Rate limiting

### Behavior Settings Tab

#### Processing Options
- **Request Delay**: 0.5-10 seconds (affects speed vs. API limits)
- **Save Interval**: 1-1000 rows (affects resume capability)
- **Max Retries**: 1-10 attempts for failed requests

#### Image Settings
- **Max Width/Height**: 10-1000 pixels (affects Excel file size)
- **Image Quality**: 1-100% (higher = better quality, larger files)

### UI Settings Tab

#### Appearance
- **Theme**: System, Light, or Dark
- **Show Notifications**: Enable/disable popup notifications
- **Minimize to Tray**: Keep running in system tray

#### File Management
- **Default Input Folder**: Pre-select folder for files
- **Remember Last Folder**: Reopen last used folder
- **Auto-open Output**: Open folder after processing

## Processing Files

### Step-by-Step Process

1. **Select Input File**
   - Click "Browse" or use File → Open File
   - Select your Excel file with phone numbers
   - The app validates the file structure

2. **Start Processing**
   - Click "Start Processing"
   - The app will:
     - Look up each phone number via API
     - Download and embed profile images
     - Save progress periodically

3. **Monitor Progress**
   - Watch the progress bars
   - Read the log for details
   - Use Stop/Pause if needed

4. **Get Results**
   - Output file saved as `[original_name]_processed.xlsx`
   - Contains original data + lookup results + embedded images

### Output File Structure

The processed file includes:

| Column | Description |
|--------|-------------|
| Number | Original phone number |
| Lookup_Status | Success/Error status |
| Full_Name | Primary name from lookup |
| Other_Names | Alternative names (pipe-separated) |
| Image_URLs | Profile image URLs (pipe-separated) |
| Base64_Images | Embedded image data |
| Lookup_Timestamp | When lookup was performed |
| Error_Message | Detailed error if any |

### Processing Controls

#### Start/Stop/Pause
- **Start**: Begin or resume processing
- **Stop**: Halt processing immediately
- **Pause**: Temporarily pause (resume later)

#### Progress Indicators
- **Overall Progress**: Complete process percentage
- **Current Progress**: Current operation percentage
- **Status Messages**: What's happening now

## API Usage Management

### Understanding Usage Statistics

#### Current Month
- **Requests This Month**: Total API calls in current month
- **Daily Average**: Average requests per day
- **Projected Monthly**: Estimated total based on current rate

#### Historical Data
- **Previous Month**: Usage from last month
- **All Time Total**: Lifetime API requests
- **Usage Trend**: 6-month usage history

### Setting Usage Limits

1. **Configure Limits**
   - Go to Settings → Configuration
   - Set "Max Requests Per Minute"
   - The app will enforce this limit

2. **Monitor Usage**
   - Watch the usage counter in main window
   - Set personal limits based on your API plan

3. **Usage Alerts**
   - Visual indicators when approaching limits
   - Color-coded usage display
   - Projection warnings

### Resetting Counters

#### Current Month Reset
- Settings → Reset API Counter
- Only affects current month
- Previous data preserved

#### Why Reset?
- New billing cycle
- Testing purposes
- Account changes

## Advanced Features

### Resume Capability

The application can resume interrupted processing:

- **Auto-save**: Progress saved every N rows
- **Resume**: Start with same file to continue
- **Skip processed**: Already processed numbers are skipped

### Batch Processing

For large files:
- Process in chunks using Save Interval
- Stop and resume as needed
- Monitor memory usage for very large files

### Custom Configuration

#### Advanced Settings
- **Proxy Support**: Configure HTTP proxy
- **Webhook Integration**: Get notifications
- **Log Level**: Control logging detail
- **Cache Settings**: Manage image caching

#### Export/Import Configuration
- **Export**: Save settings to file
- **Import**: Load settings from file
- **Backup**: Keep configuration backups

## Troubleshooting

### Common Issues and Solutions

#### API Errors
**Problem**: "API Error" messages
**Solution**:
- Verify API key is correct
- Check internet connection
- Ensure API account has credits
- Check RapidAPI status page

#### File Processing Errors
**Problem**: "Invalid file format"
**Solution**:
- Ensure file is Excel format (.xlsx, .xls)
- Verify 'Number' column exists
- Check file isn't corrupted
- Ensure Excel isn't open during processing

#### Performance Issues
**Problem**: Slow processing
**Solution**:
- Increase Request Delay for stability
- Reduce Save Interval for more frequent saves
- Close other applications
- Check network connection

#### Image Embedding Issues
**Problem**: Images not embedding
**Solution**:
- Check image URL accessibility
- Verify base64 data format
- Increase timeout settings
- Check available disk space

### Log Files

#### Location
- Windows: `%LOCALAPPDATA%\PhoneLookupTool\logs\`
- macOS: `~/Library/Application Support/PhoneLookupTool/logs/`
- Linux: `~/.local/share/PhoneLookupTool/logs/`

#### Important Logs
- `application.log`: Main application log
- `phone_lookup.log`: API call details
- `image_embedder.log`: Image processing details
- `usage_tracker.log`: API usage tracking

### Getting Help

When contacting support, provide:
1. Application version
2. Operating system
3. Error messages from logs
4. Steps to reproduce the issue
5. Sample file (if possible)

## Best Practices

### Data Preparation
- **Clean your data**: Remove invalid numbers before processing
- **Use consistent formats**: Stick to one phone number format
- **Backup original files**: Keep copies of input files
- **Test with small files**: Verify setup with 5-10 numbers first

### API Usage
- **Respect rate limits**: Use appropriate request delays
- **Monitor usage**: Keep track of your API consumption
- **Plan batches**: Process during off-peak hours if needed
- **Use pause/resume**: For large files, break into sessions

### Performance Optimization
- **Adjust settings**: Balance speed vs. stability
- **Close Excel**: Ensure Excel isn't running during processing
- **Sufficient RAM**: 4GB+ recommended for large files
- **Fast storage**: SSD recommended for better performance

### File Management
- **Organize files**: Keep input/output files in separate folders
- **Regular cleanup**: Remove old processed files
- **Backup configuration**: Export settings periodically
- **Update regularly**: Keep application updated

### Security
- **Protect API keys**: Don't share configuration files
- **Secure files**: Store sensitive data appropriately
- **Regular updates**: Keep software patched
- **Monitor usage**: Watch for unusual activity

---

## Quick Reference

### Keyboard Shortcuts
- `Ctrl+O`: Open file
- `Ctrl+S`: Settings
- `Ctrl+Q`: Quit
- `Space`: Start/Pause processing

### Default Settings
- Request Delay: 1.5 seconds
- Save Interval: 10 rows
- Max Image Size: 100x100 pixels
- Max Requests/Minute: 60

### File Naming
- Input: `your_file.xlsx`
- Output: `your_file_processed.xlsx`
- Logs: `application.log`, `phone_lookup.log`, etc.

### Support Resources
- Documentation: `docs/` folder
- Logs: Application data directory
- Updates: Check GitHub releases
