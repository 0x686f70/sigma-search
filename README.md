# Sigma Search Application

A modern, web-based application for searching, viewing, and converting Sigma security detection rules to Lucene queries with structured visualization.

## Features

- **Sigma Rule Search**: Full-text search across Sigma rules with category and subcategory filtering
- **Multiple Rule Sources**: Automatically loads rules from multiple directories:
  - Standard rules (`rules/`)
  - Emerging threats (`rules-emerging-threats/`)
  - Threat hunting (`rules-threat-hunting/`)
  - Compliance rules (`rules-compliance/`)
  - DFIR rules (`rules-dfir/`)
  - Custom rules (`customs/`)
- **Lucene Conversion**: Convert Sigma rules to Lucene queries for SIEM platforms
- **Structured Query View**: Visual representation of parsed Lucene queries with hierarchical display
- **Custom Rules Management**: Create, edit, and manage custom Sigma rules
- **Modern UI**: Responsive web interface with intuitive navigation
- **Query Parsing**: Advanced Lucene query parser with support for complex nested structures

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sigma_search_app
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   
   **Development mode (with auto-reload):**
   ```bash
   python app.py
   ```
   
   **Production mode (without auto-reload):**
   ```bash
   set FLASK_DEBUG=False
   python app.py
   ```

The application will be available at `http://127.0.0.1:5000`

**Note:** In development mode, the application will automatically reload when you make changes to Python files. You don't need to restart the server!

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `production` for production deployment
- `FLASK_SECRET_KEY`: Secret key for Flask sessions (auto-generated if not set)
- `FLASK_DEBUG`: Set to `true` to enable debug mode
- `FLASK_HOST`: Host to bind to (default: 127.0.0.1)
- `FLASK_PORT`: Port to bind to (default: 5000)

### Production Deployment

For production deployment, set the following environment variables:

```bash
export FLASK_ENV=production
export FLASK_SECRET_KEY=your-secure-secret-key
export FLASK_DEBUG=false
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
```

## Usage

### Basic Search

1. **Browse Rules**: Use the category and subcategory filters to navigate Sigma rules
2. **Search**: Use the search bar to find specific rules by title, description, or content
3. **View Rules**: Click on any rule to view its full YAML content

### Lucene Conversion

1. **Convert to Lucene**: Click "Convert to Lucene" to generate Lucene queries
2. **Structured View**: Click "Structured View" to see a parsed, hierarchical representation
3. **Show Raw**: View the original Lucene query string
4. **Copy Queries**: Copy individual parts or entire queries to clipboard

### Custom Rules

1. **Create Rules**: Add new custom Sigma rules through the web interface
2. **Edit Rules**: Modify existing custom rules
3. **Delete Rules**: Remove custom rules when no longer needed

## Project Structure

```
sigma_search_app/
├── app/                    # Application package
│   ├── __init__.py        # Application factory
│   ├── config.py          # Configuration management
│   ├── field_mappings.py  # Sigma to Stellar field mappings
│   ├── lucene_converter.py # Sigma to Lucene conversion logic
│   ├── query_parser.py    # Lucene query parsing and structuring
│   ├── rule_loader.py     # Sigma rule loading and searching
│   ├── rule_processor.py  # Rule grouping and sorting
│   ├── rules_manager.py   # Rule state management
│   ├── update_rules.py    # Rule update functionality
│   └── routes/            # Flask route blueprints
│       ├── __init__.py    # Route initialization
│       ├── main.py        # Main application routes
│       ├── conversion.py  # Lucene conversion routes
│       ├── custom_rules.py # Custom rule management routes
│       ├── rule_yaml.py   # Rule content viewing routes
│       └── update.py      # Rule update routes
├── static/                 # Static assets
│   ├── app.js            # Main application JavaScript
│   ├── style.css         # Application styles
│   └── favicon.svg       # Application favicon
├── templates/             # HTML templates
│   └── index.html        # Main application template
├── sigma_rules/          # Sigma rule repository
│   ├── windows/          # Standard Windows rules
│   ├── linux/            # Standard Linux rules
│   ├── cloud/            # Standard cloud rules
│   ├── customs/          # Custom user rules
│   ├── rules-emerging-threats/  # Emerging threat rules
│   ├── rules-threat-hunting/    # Threat hunting rules
│   └── ...               # Other rule categories
├── logs/                 # Application logs (auto-created)
├── app.py                # Application entry point
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Development

### Hot Reload

The application runs in debug mode by default with auto-reload enabled. When you modify Python files, the server will automatically restart:

```bash
# Just run normally - auto-reload is enabled by default
python app.py
```

**What triggers reload:**
- ✅ Python files (`.py`) in `app/` directory
- ✅ Route changes, model updates, utility functions
- ❌ Static files (`.js`, `.css`) - refresh browser manually
- ❌ Templates (`.html`) - refresh browser manually

**To disable auto-reload (production):**
```bash
# Windows
set FLASK_DEBUG=False
python app.py

# Linux/Mac
export FLASK_DEBUG=false
python app.py
```

### Code Quality

- **Type Hints**: Use Python type hints for better code documentation
- **Error Handling**: Implement proper exception handling and logging
- **Code Style**: Follow PEP 8 Python style guidelines
- **Documentation**: Document all public functions and classes

### Testing

Run the application in development mode:

```bash
python app.py
```

### Logging

Application logs are stored in the `logs/` directory with automatic rotation:
- Log files are limited to 10MB each
- Up to 5 backup files are maintained
- Logs include timestamps, log levels, and source information

## API Endpoints

### Main Routes

- `GET /` - Main application interface
- `GET /favicon.ico` - Application favicon

### Rule Management

- `GET /rule_yaml` - View rule YAML content
- `POST /update_rules` - Update Sigma rules repository (~15-20 seconds)
  - Downloads: standard rules + emerging threats + threat hunting + compliance + DFIR rules
  - Automatically clears cache after update
  - Timing breakdown:
    - Git clone: ~3s
    - Sparse checkout: ~7s
    - File operations: ~3-5s
    - Cache clear: ~0.1s

### Lucene Conversion

- `GET /convert_to_lucene` - Convert Sigma rule to Lucene query
- `GET /convert_to_structured` - Convert to structured query format

### Custom Rules

- `GET /custom_rules` - List custom rules
- `GET /custom_rules/<filename>` - Get custom rule content
- `POST /custom_rules` - Create/update custom rule
- `DELETE /custom_rules/<filename>` - Delete custom rule

## Dependencies

### Core Dependencies

- **Flask**: Web framework for the application
- **PyYAML**: YAML parsing for Sigma rules
- **Werkzeug**: WSGI utilities for Flask

### Version Requirements

- Flask >= 2.3.0, < 3.0.0
- PyYAML >= 6.0, < 7.0
- Werkzeug >= 2.3.0, < 3.0.0

## Security Considerations

- **Secret Key**: Use environment variables for Flask secret keys in production
- **Input Validation**: All user inputs are properly validated and sanitized
- **File Access**: File access is restricted to designated directories
- **Session Security**: Secure session configuration with HTTP-only cookies

## Troubleshooting

### Common Issues

1. **Rules Not Loading**: Check that the `sigma_rules/` directory exists and contains valid YAML files. The application automatically scans these subdirectories:
   - `rules/` - Standard Sigma rules
   - `rules-emerging-threats/` - Emerging threat detection rules
   - `rules-threat-hunting/` - Threat hunting rules
   - `rules-compliance/` - Compliance-focused rules
   - `rules-dfir/` - Digital forensics and incident response rules
   - `customs/` - Custom user-created rules
2. **Conversion Errors**: Ensure Sigma rules have valid YAML syntax and required fields
3. **Permission Errors**: Verify the application has read access to the rules directory and all subdirectories

### Logs

Check the `logs/sigma_app.log` file for detailed error information and debugging details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Open an issue on the project repository

## Performance

### Startup Time Optimization

The application uses intelligent caching to dramatically improve startup time:

- **First run:** ~13 seconds (loads and caches 4,000+ rules)
- **Subsequent runs:** ~0.7 seconds (loads from cache)
- **Cache invalidation:** Automatic when rules change

**Cache location:** `.cache/` directory (auto-created)

**Clear cache:**
```bash
# Via API
curl -X POST http://127.0.0.1:5000/api/cache/clear

# Or manually delete
rm -rf .cache
```

**Disable caching (not recommended):**
```bash
set SIGMA_OPTIMIZED_LOADING=False
python app.py
```

## Changelog

### Version 1.2.0 (2025-01-22)
- **Performance:** Added rule caching system - 14x faster startup (10s → 0.7s)
- **Performance:** Parallel rule loading with ThreadPoolExecutor
- **Performance:** Automatic cache invalidation on rule changes
- **API:** Added `/api/cache/clear` endpoint for cache management

### Version 1.1.0 (2025-01-22)
- **Multi-Source Rule Support**: Added support for multiple Sigma rule sources
  - Standard rules (windows, linux, cloud, etc.)
  - Emerging threats rules (`rules-emerging-threats/`)
  - Threat hunting rules (`rules-threat-hunting/`)
  - Compliance rules (`rules-compliance/`)
  - DFIR rules (`rules-dfir/`)
- **Enhanced Update System**: Single update operation now downloads all rule categories
- **Improved Logging**: Detailed statistics showing rules by source
- **Better Documentation**: Added `RULES_STRUCTURE.md` and `UPGRADE_SUMMARY.md`
- **Diagnostic Tools**: Added helper scripts for checking and testing rule loading
- **Backward Compatible**: Existing installations work without changes

### Version 1.0.0
- Initial release with core Sigma rule search functionality
- Lucene query conversion and structured visualization
- Custom rule management system
- Modern, responsive web interface
