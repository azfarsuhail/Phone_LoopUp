# Phone Number Lookup Tool

A professional desktop application for looking up phone numbers using the Eyecon API and embedding profile images directly into Excel files.

## 🚀 Features

- **Phone Number Lookup**: Look up phone numbers using the Eyecon API
- **Image Embedding**: Automatically embed profile images into Excel files
- **API Usage Tracking**: Monitor and limit monthly API usage
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Secure Configuration**: Encrypted storage of API keys and sensitive data
- **User-Friendly GUI**: Simple interface built with tkinter
- **Resume Capability**: Continue processing from where you left off

## 📋 Requirements

- Python 3.8 or higher
- Eyecon API account and API key

## 🛠️ Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## 📖 Usage

See [USER_GUIDE.md](USER_GUIDE.md) for comprehensive usage instructions.

## 🏗️ Project Structure

```
PhoneLookupTool/
├── main.py                 # Main application entry point
├── modules/               # Core application modules
│   ├── phone_lookup.py    # Phone number lookup functionality
│   ├── image_embedder.py  # Excel image embedding
│   ├── usage_tracker.py   # API usage tracking
│   ├── config_manager.py  # Configuration management
│   └── path_utils.py      # Cross-platform path handling
├── tests/                 # Unit tests
├── docs/                  # Documentation
└── assets/               # Application icons and images
```

## 🔧 Configuration

1. Launch the application
2. Go to Settings → API Settings
3. Enter your Eyecon API key
4. Configure processing parameters as needed

## 📊 API Usage Tracking

- Tracks monthly API request counts
- Shows daily averages and projections
- Configurable usage limits
- Visual alerts when approaching limits

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
- Ensure your API key is valid and has sufficient credits
- Check your internet connection

**Excel File Issues**
- Ensure input files have a 'Number' column
- Close Excel before processing files

**Permission Errors**
- Run as administrator if needed
- Check file/folder permissions

### Logs

Application logs are stored in:
- Windows: `%LOCALAPPDATA%\PhoneLookupTool\logs\`
- macOS: `~/Library/Application Support/PhoneLookupTool/logs/`
- Linux: `~/.local/share/PhoneLookupTool/logs/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the logs for error messages
2. Verify your API key is correct
3. Ensure you have the latest version
4. Contact support with your log files

## 🔄 Version History

- **v1.0.0** - Initial release with basic lookup and image embedding
- **v1.1.0** - Added API usage tracking and configuration management
