# Phone Number Lookup Tool

A professional desktop application for looking up phone numbers using the Eyecon API and embedding profile images directly into Excel files.

![Application Screenshot](assets/screenshot.png)

## 🚀 Features

- **📞 Phone Number Lookup**: Look up phone numbers using the Eyecon API
- **🖼️ Image Embedding**: Automatically embed profile images into Excel files
- **📊 API Usage Tracking**: Monitor and limit monthly API usage with visual indicators
- **🔒 Secure Configuration**: Encrypted storage of API keys and sensitive data
- **🎨 User-Friendly GUI**: Simple and intuitive interface built with tkinter
- **⏯️ Resume Capability**: Continue processing from where you left off
- **🌙 Dark/Light Theme**: Choose your preferred theme
- **📁 Cross-Platform**: Works on Windows, macOS, and Linux

## 📋 Requirements

- **Python**: 3.8 or higher
- **Eyecon API Account**: Get your API key from [RapidAPI Eyecon](https://rapidapi.com/eyecon/api/eyecon)

## 🛠️ Installation

### Method 1: From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/azfarsuhail/Phone_LoopUp.git
cd Phone_LoopUp

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Method 2: Using Executable (For End Users)

Download the latest release from the [Releases page](https://github.com/azfarsuhail/Phone_LoopUp/releases) and run the executable for your platform.

## 📖 Quick Start Guide

### 1. First Time Setup

1. **Launch the application**
2. **Configure API Settings**:
   - Go to `Settings → Configuration`
   - Enter your Eyecon API key
   - Set your monthly API limit
   - Configure other preferences
   - Click `Save`

### 2. Prepare Your Data

Create an Excel file with a `Number` column containing phone numbers:

| Number       |
|-------------|
| 3001234567  |
| 3007654321  |
| 3009876543  |

**Supported Formats**: Numbers starting with `3` (e.g., `3XXXXXXXXX`)

### 3. Process Your File

1. **Upload File**: Click `Browse` and select your Excel file
2. **Start Processing**: Click `Start Processing`
3. **Monitor Progress**: Watch the progress bars and log messages
4. **Get Results**: Output file saved as `[original_name]_processed.xlsx`

## ⚙️ Configuration

### API Settings
- **API Key**: Your Eyecon API key from RapidAPI
- **Monthly Limit**: Maximum API requests per month
- **Request Delay**: Seconds between API calls (1.5 recommended)

### Processing Settings
- **Save Interval**: Rows processed between auto-saves
- **Max Retries**: Number of retry attempts for failed requests
- **Country Code**: Default country code (92 for Pakistan)

### Image Settings
- **Max Width/Height**: Image dimensions for embedding
- **Image Quality**: JPEG quality percentage

### UI Settings
- **Theme**: System, Light, or Dark mode
- **Notifications**: Enable/disable popup notifications
- **Auto-open Output**: Open folder after processing

## 📊 API Usage Management

The application tracks your API usage with:

- **Current Month Counter**: Real-time usage tracking
- **Color Coding**: Green/Yellow/Red indicators based on usage percentage
- **Progress Bar**: Visual representation of monthly limit
- **Daily Average**: Average requests per day
- **All-Time Total**: Lifetime API requests

### Setting Limits
Configure your monthly limit in `Settings → API Settings`. When the limit is reached:
- Processing stops automatically
- Popup asks to increase limit or continue
- Current progress is saved

## 🗂️ File Formats

### Input File Requirements
- **Format**: Excel (.xlsx, .xls)
- **Required Column**: `Number`
- **Phone Format**: Numbers starting with `3` (e.g., `3001234567`)

### Output File Structure
The processed file includes:

| Column | Description |
|--------|-------------|
| `Number` | Original phone number |
| `Status` | Lookup status (Success/Error) |
| `Name_1` to `Name_10` | Extracted names |
| `Image_1` to `Image_10` | Profile image URLs |
| `b64_1` to `b64_3` | Base64 encoded images |

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
- Ensure your API key is valid and has sufficient credits
- Check your internet connection
- Verify API key in Settings

**File Processing Errors**
- Ensure file has a `Number` column
- Close Excel before processing files
- Check file is not corrupted

**Permission Errors**
- Run as administrator if needed
- Check file/folder permissions

### Log Files

Application logs are stored in:
- **Windows**: `%LOCALAPPDATA%\PhoneLookupTool\logs\`
- **macOS**: `~/Library/Application Support/PhoneLookupTool/logs/`
- **Linux**: `~/.local/share/PhoneLookupTool/logs/`

Important logs:
- `application.log` - Main application log
- `phone_lookup.log` - API call details
- `image_embedder.log` - Image processing details

## 🔧 Building from Source

### Prerequisites
- Python 3.8+
- pip
- Git

### Build Steps

```bash
# Clone repository
git clone https://github.com/azfarsuhail/Phone_LoopUp.git
cd Phone_LoopUp

# Install build dependencies
pip install pyinstaller

# Build executable
pyinstaller build.spec

# Executable will be in dist/ folder
```

### Development

```bash
# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Code formatting
black .
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. **Check the logs** for error messages
2. **Verify your API key** is correct and active
3. **Check the GitHub Issues** for similar problems
4. **Contact Support** with:
   - Your operating system and version
   - Python version
   - Error messages from logs
   - Steps to reproduce the issue

### Resources
- **Documentation**: [User Guide](docs/USER_GUIDE.md) • [Installation Guide](docs/INSTALL.md)
- **Issues**: [GitHub Issues](https://github.com/azfarsuhail/Phone_LoopUp/issues)
- **Releases**: [Latest Release](https://github.com/azfarsuhail/Phone_LoopUp/releases)

## 🔄 Version History

- **v1.0.0** - Initial release with basic lookup and image embedding
- **v1.1.0** - Added API usage tracking and configuration management
- **v1.2.0** - Enhanced GUI with themes and improved error handling

---

**Note**: This application requires a valid Eyecon API key from RapidAPI. The free tier may have limitations on the number of requests per month.

**Disclaimer**: This tool is for legitimate use only. Users are responsible for complying with applicable laws and API terms of service.
```

## Alternative Minimal README:

```markdown
# Phone Lookup Tool

Desktop application for phone number lookup and image embedding in Excel files.

## Quick Start

1. Get API key from [RapidAPI Eyecon](https://rapidapi.com/eyecon/api/eyecon)
2. Download executable from [Releases](https://github.com/azfarsuhail/Phone_LoopUp/releases)
3. Run application and configure API key in Settings
4. Upload Excel file with 'Number' column
5. Click Start Processing

## Features

- Phone number lookup via Eyecon API
- Automatic image embedding in Excel
- API usage tracking and limits
- Cross-platform support
- Secure configuration storage

## Requirements

- Windows 7+/macOS 10.12+/Linux
- Eyecon API account
- Excel files with 'Number' column

## Support

- [User Guide](docs/USER_GUIDE.md)
- [Issues](https://github.com/azfarsuhail/Phone_LoopUp/issues)