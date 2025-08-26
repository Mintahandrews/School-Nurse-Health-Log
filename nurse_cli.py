import os
import sys
from datetime import datetime

# Import the existing functions from the original script
from excel_batch_operations_enhanced import (
    EXCEL_FILE, initialize_excel_file, add_record, get_all_records,
    find_records, update_record, delete_record
)

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print a formatted header."""
    clear_screen()
    print("=" * 60)
    print(f"{title:^60}")
    print("=" * 60)
    print()

def print_record(record):
    """Print a single record in a readable format."""
    print("-" * 60)
    for key, value in record.items():
        if value:  # Only print fields with values
            print(f"{key:30}: {value}")
    print("-" * 60)

def input_field(prompt, required=True):
    """Get input for a field with optional validation."""
    while True:
        value = input(prompt).strip()
        if not value and required:
            print("This field is required. Please enter a value.")
        else:
            return value if value else ""

def input_date(prompt, default=None):
    """Get a date input with validation."""
    while True:
        date_str = input(f"{prompt} [YYYY-MM-DD]: ").strip()
        if not date_str and default:
            return default
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")

def input_time(prompt, default=None):
    """Get a time input with validation."""
    while True:
        time_str = input(f"{prompt} [HH:MM or HH:MM AM/PM]: ").strip()
        if not time_str and default:
            return default
        try:
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                datetime.strptime(time_str, "%I:%M %p")
            else:
                datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            print("Invalid time format. Please use HH:MM or HH:MM AM/PM format.")

def input_yes_no(prompt, default_yes=False):
    """Get a yes/no input."""
    while True:
        choice = input(f"{prompt} (Y/N): ").strip().upper()
        if not choice and default_yes is not None:
            return "Yes" if default_yes else "No"
        if choice in ('Y', 'YES'):
            return "Yes"
        elif choice in ('N', 'NO'):
            return "No"
        print("Please enter Y or N.")

def add_new_record():
    """Add a new health record."""
    print_header("ADD NEW HEALTH RECORD")
    
    record = {}
    
    # Basic Information
    print("\n[PATIENT INFORMATION]")
    record["Full Name"] = input_field("Patient's Full Name: ")
    record["Date of Birth"] = input_date("Date of Birth (YYYY-MM-DD)")
    record["Age"] = input_field("Age: ", required=False)
    record["Gender"] = input_field("Gender: ", required=False)
    record["Grade/Year Level"] = input_field("Grade/Year Level: ", required=False)
    
    # Visit Information
    print("\n[VISIT INFORMATION]")
    record["Date of Visit"] = input_date("Date of Visit", datetime.now().strftime("%Y-%m-%d"))
    record["Time of Visit"] = input_time("Time of Visit", datetime.now().strftime("%H:%M"))
    record["Nurse Name/ID"] = input_field("Nurse Name/ID: ")
    
    # Reason for Visit
    print("\n[REASON FOR VISIT]")
    print("1. Illness")
    print("2. Injury")
    print("3. Medication")
    print("4. Follow-up")
    print("5. Screening")
    print("6. Other")
    
    reason_choice = input("Select reason (1-6): ").strip()
    reasons = ["Illness", "Injury", "Medication", "Follow-up", "Screening", "Other"]
    record["Visit Reason Category"] = reasons[int(reason_choice)-1] if reason_choice.isdigit() and 1 <= int(reason_choice) <= 6 else "Other"
    
    # Vital Signs
    print("\n[VITAL SIGNS]")
    record["Temperature (°C)"] = input_field("Temperature (°C): ", required=False)
    record["Pulse (bpm)"] = input_field("Pulse (bpm): ", required=False)
    record["Blood pressure (mmHg)"] = input_field("Blood pressure (mmHg): ", required=False)
    
    # Notes
    print("\n[NOTES]")
    record["Notes/Comments"] = input("Additional notes: ")
    
    # Save the record
    try:
        add_record(record)
        print("\nRecord added successfully!")
    except Exception as e:
        print(f"\nError adding record: {str(e)}")
    
    input("\nPress Enter to continue...")

def view_records():
    """View all records."""
    print_header("VIEW ALL RECORDS")
    
    records = get_all_records()
    
    if not records:
        print("No records found.")
        input("\nPress Enter to continue...")
        return
    
    for i, record in enumerate(records, 1):
        print(f"\n[RECORD {i}]")
        print(f"ID: {record.get('Patient ID', 'N/A')}")
        print(f"Name: {record.get('Full Name', 'N/A')}")
        print(f"Date: {record.get('Date of Visit', 'N/A')} {record.get('Time of Visit', '')}")
        print(f"Reason: {record.get('Visit Reason Category', 'N/A')}")
        print(f"Nurse: {record.get('Nurse Name/ID', 'N/A')}")
    
    input("\nPress Enter to continue...")

def search_records():
    """Search for records."""
    print_header("SEARCH RECORDS")
    
    search_term = input("Enter search term (name, ID, or nurse): ").strip()
    
    if not search_term:
        print("Please enter a search term.")
        input("\nPress Enter to continue...")
        return
    
    records = find_records({"Full Name": search_term}) or \
              find_records({"Patient ID": search_term}) or \
              find_records({"Nurse Name/ID": search_term})
    
    if not records:
        print("No matching records found.")
    else:
        print(f"\nFound {len(records)} matching record(s):\n")
        for i, record in enumerate(records, 1):
            print(f"[RECORD {i}]")
            print(f"ID: {record.get('Patient ID', 'N/A')}")
            print(f"Name: {record.get('Full Name', 'N/A')}")
            print(f"Date: {record.get('Date of Visit', 'N/A')} {record.get('Time of Visit', '')}")
            print(f"Reason: {record.get('Visit Reason Category', 'N/A')}")
            print(f"Nurse: {record.get('Nurse Name/ID', 'N/A')}")
            print()
    
    input("\nPress Enter to continue...")

def main_menu():
    """Display the main menu and handle user input."""
    while True:
        print_header("SCHOOL NURSE HEALTH LOG")
        print("1. Add New Record")
        print("2. View All Records")
        print("3. Search Records")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            add_new_record()
        elif choice == '2':
            view_records()
        elif choice == '3':
            search_records()
        elif choice == '4':
            print("\nThank you for using the School Nurse Health Log System. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # Initialize the Excel file if it doesn't exist
    if not os.path.exists(EXCEL_FILE):
        initialize_excel_file()
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        input("Press Enter to exit...")
