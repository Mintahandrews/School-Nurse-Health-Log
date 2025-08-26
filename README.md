# School Nurse Health Log

A Flask-based web application for managing school nurse health records.

## Features

- Add, edit, view, and delete health records
- Search functionality by name, patient ID, or nurse name
- Import/export Excel functionality
- Responsive web interface with modern design

## Project Structure

The application follows a modular structure:

```
/Nurse Records
├── app/                      # Application package
│   ├── __init__.py          # Flask app initialization
│   ├── config/              # Configuration settings
│   │   └── config.py
│   ├── controllers/         # Route handlers
│   │   └── main.py
│   ├── forms/               # Form definitions
│   │   └── forms.py
│   ├── models/              # Database models
│   │   └── db.py
│   ├── static/              # Static assets
│   │   ├── css/
│   │   └── js/
│   ├── templates/           # HTML templates
│   └── utils/               # Helper functions
│       └── excel_utils.py
├── instance/                # Instance-specific data
│   └── nurse_records.db     # SQLite database (created automatically)
├── requirements.txt         # Dependencies
└── run.py                   # Application entry point
```

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python run.py
   ```
   or use the provided shell script:
   ```
   ./run.sh
   ```
3. Open your web browser and navigate to: http://127.0.0.1:5000

### Web Application Features

- **Dashboard**: View all health records in a sortable table format
- **Add Record**: Create new student health records with comprehensive information
- **View Record**: See detailed information for each visit
- **Edit/Delete**: Manage existing records
- **Search**: Quickly find records by patient name, ID, or nurse name
- **Excel Integration**: Import existing records from Excel and export to Excel

### Data Storage

The web application stores all data in an SQLite database (`nurse_records.db`) which is automatically created when you first run the application.

## Command-line Interface (CLI)

In addition to the web application, a separate CLI application is available that manages records directly in an Excel file. This is useful for batch operations or scripting.

### CLI Files

The following files provide CLI functionality:
- `excel_batch_operations_enhanced.py` - Main CLI tool for Excel operations
- `nurse_cli.py` - Alternative CLI interface

### Initialize the Excel file
```bash
python3 excel_batch_operations_enhanced.py init
```

### Add a new record
```bash
python3 excel_batch_operations_enhanced.py add --data '{"Full Name":"John Doe", "Date of Visit":"2025-08-04", "Time of Visit":"10:00 AM", "Nurse Name/ID":"NURSE001"}'
```

### List all records
```bash
python3 excel_batch_operations_enhanced.py list
```

### Find records
```bash
# Basic search (case-insensitive partial match)
python3 excel_batch_operations_enhanced.py find --data '{"Full Name":"john"}'

# Exact match search
python3 excel_batch_operations_enhanced.py find --data '{"Full Name":"John Doe"}' --exact_match
```

### Update a record
```bash
python3 excel_batch_operations_enhanced.py update --patient_id "SID20250804105012345" --data '{"Temperature (°C)":"37.2"}'
```

### Delete a record
```bash
python3 excel_batch_operations_enhanced.py delete --patient_id "SID20250804105012345"
```

### CLI Data Storage
The CLI application stores all data in `SchoolNurse_HealthLog.xlsx` in the same directory as the script.

## Data Migration

You can move data between the CLI and web application:

1. **CLI to Web**: Use the web app's import feature to upload the Excel file
2. **Web to CLI**: Export from the web app to Excel, which can then be used with the CLI tool
