# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-30

### Added
- Initial release
- Clean Architecture implementation (Domain, Application, Infrastructure, Presentation layers)
- PyQt6 GUI with multi-client tab system
- IMAP email processing (Outlook/Office365)
- UBL 2.1 XML parser for Colombian electronic invoices
- CSV export with customizable format (delimiter, decimal separator, precision)
- SQLite database for tracking processed emails
- Automatic update system from GitHub Releases
- Comprehensive logging system
- Auto-processing mode with configurable intervals
- System tray integration
- Configuration management via JSON files
- Environment variables support for credentials
- First client: Comercializadora Triple A

### Features
- **Email Processing**: Automatic fetching and processing of invoices from email
- **ZIP Extraction**: Automatic extraction of PDF and XML files from ZIP attachments
- **Invoice Parsing**: UBL 2.1 XML parsing with full support for Colombian format
- **CSV Export**: Configurable CSV output with 22 fields
- **Duplicate Prevention**: SQLite-based tracking to avoid processing same email twice
- **Multi-client Support**: Easy addition of new clients via configuration
- **Auto-update**: GitHub-based automatic updates with user confirmation
- **Logging**: Rotating logs with multiple levels (DEBUG, INFO, WARNING, ERROR)
- **GUI**: Modern PyQt6 interface with tabs, counters, and real-time logs

### Technical Details
- Python 3.9+
- PyQt6 for GUI
- lxml for XML parsing
- imaplib for email
- sqlite3 for database
- requests for GitHub API
- PyInstaller for executable creation

### Known Issues
- None

[1.0.0]: https://github.com/LuisVeraVR/medellin_sae/releases/tag/v1.0.0
