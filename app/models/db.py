import os
import sqlite3
from datetime import datetime
import random
import string
import psycopg2
from psycopg2.extras import DictCursor
from flask import current_app

def get_db_connection():
    """Create and return a database connection (SQLite for all environments)."""
    # Always use SQLite to keep schema and migrations consistent across envs.
    # Render is configured with a persistent disk mounted at instance/.
    db_file = current_app.config['DB_FILE']
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the required schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if records table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='records'
    """)
    table_exists = cursor.fetchone()
    
    # Get current timestamp
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # If table exists, migrate data to a temporary table
    if table_exists:
        # Get the current schema to check if migration is needed
        cursor.execute("PRAGMA table_info(records)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # If old schema is detected, migrate data
        if 'pulse' in columns and 'heart_rate' not in columns:
            # Create a backup of the old data
            cursor.execute('CREATE TABLE IF NOT EXISTS records_backup AS SELECT * FROM records')
            
            # Create a new table with updated schema
            cursor.execute('ALTER TABLE records RENAME TO old_records')
            conn.commit()
        else:
            # Table exists but has the new schema, no migration needed
            return
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS records (
        -- Identification
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE,
        
        -- Student Demographics
        full_name TEXT NOT NULL,
        date_of_birth TEXT,
        age INTEGER,
        gender TEXT,
        grade_level TEXT,
        
        -- Contact Information
        parent_primary_name TEXT,
        parent_primary_phone TEXT,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        
        -- Visit Information
        academic_year TEXT,
        academic_term TEXT,
        date_of_visit TEXT NOT NULL,
        time_of_visit TEXT NOT NULL,
        brought_in_by TEXT,
        nurse_name TEXT NOT NULL,
        visit_reason_category TEXT,
        severity_level TEXT,
        visit_details TEXT,
        
        -- Vital Signs
        temperature REAL,  -- in Celsius
        heart_rate INTEGER,  -- bpm (replaces pulse)
        respiratory_rate INTEGER,  -- breaths per minute
        oxygen_saturation REAL,  -- percentage
        blood_pressure_systolic INTEGER,  -- mmHg
        blood_pressure_diastolic INTEGER,  -- mmHg
        height REAL,  -- in inches
        weight REAL,  -- in lbs
        bmi REAL,  -- kg/m²
        pain_scale INTEGER,  -- 0-10 scale
        pain_location TEXT,  -- location of pain
        
        -- Presenting Complaints
        presenting_complaints TEXT,
        other_complaint_details TEXT,
        complaint_background TEXT,
        
        -- Medical History
        past_medical_history TEXT,
        known_allergies TEXT,
        current_medications TEXT,
        special_medical_needs BOOLEAN DEFAULT 0,
        chronic_conditions TEXT,
        
        -- Assessment & Care
        nurse_observations TEXT,
        interventions_provided TEXT,
        medications_administered TEXT,
        next_steps TEXT,
        other_next_step_details TEXT,
        referral_type TEXT,
        follow_up_date TEXT,
        
        -- Admission to Sick Bay
        admission_date TEXT,
        admission_time TEXT,
        condition_on_admission TEXT,
        plan_of_care TEXT,
        
        -- Discharge Information
        discharge_time TEXT,
        condition_at_discharge TEXT,
        discharge_instructions TEXT,
        return_to_class_time TEXT,
        parent_notified BOOLEAN DEFAULT 0,
        parent_notification_time TEXT,
        incident_report_required BOOLEAN DEFAULT 0,
        
        -- System Fields
        notes TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    # If we migrated data, copy it to the new table
    if table_exists and 'old_records' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        # Get column names that exist in both tables
        cursor.execute('PRAGMA table_info(records)')
        new_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute('PRAGMA table_info(old_records)')
        old_columns = [col[1] for col in cursor.fetchall()]
        
        # Find common columns
        common_columns = set(new_columns).intersection(old_columns)
        common_columns.discard('id')  # Skip ID as it's auto-incremented
        
        # Build the column list for the INSERT statement
        columns_str = ', '.join(common_columns)
        placeholders = ', '.join(['?'] * len(common_columns))
        
        # Copy data from old table to new table
        cursor.execute(f'''
            INSERT INTO records ({columns_str}, created_at, updated_at)
            SELECT {columns_str}, created_at, ? 
            FROM old_records
        ''', (current_time,))
        
        # Drop the old table
        cursor.execute('DROP TABLE old_records')
    
    # Create an index on frequently queried fields
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_records_patient_id 
        ON records(patient_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_records_full_name 
        ON records(full_name)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_records_date_of_visit 
        ON records(date_of_visit)
    ''')
    
    conn.commit()
    conn.close()

def generate_patient_id():
    """Generate a unique patient ID with format: YYYYMMDD-XXXX"""
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{date_part}-{random_part}"

def create_record(record_data):
    """Create a new health record in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate a new patient ID if not provided
    if 'patient_id' not in record_data or not record_data['patient_id']:
        record_data['patient_id'] = generate_patient_id()
    
    # Set timestamps
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    record_data['created_at'] = current_time
    record_data['updated_at'] = current_time
    
    # Prepare the SQL query
    columns = ', '.join(record_data.keys())
    placeholders = ', '.join(['?'] * len(record_data))
    
    try:
        cursor.execute(
            f'INSERT INTO records ({columns}) VALUES ({placeholders})',
            list(record_data.values())
        )
        record_id = cursor.lastrowid
        conn.commit()
        return get_record_by_id(record_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_record_by_id(record_id):
    """Retrieve a health record by its ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM records WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    
    return dict(record) if record else None

def get_record_by_patient_id(patient_id):
    """Retrieve a health record by patient ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM records WHERE patient_id = ?', (patient_id,))
    record = cursor.fetchone()
    conn.close()
    
    return dict(record) if record else None

def update_record(record_id, update_data):
    """Update an existing health record"""
    if not update_data:
        return get_record_by_id(record_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update the timestamp
    update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Prepare the SQL query
    set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values())
    values.append(record_id)
    
    try:
        cursor.execute(
            f'UPDATE records SET {set_clause} WHERE id = ?',
            values
        )
        conn.commit()
        return get_record_by_id(record_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_record(record_id):
    """Delete a health record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM records WHERE id = ?', (record_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def search_records(search_term, page=1, per_page=20):
    """Search health records with pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    search_pattern = f'%{search_term}%'
    
    # Count total matching records
    cursor.execute('''
        SELECT COUNT(*) FROM records 
        WHERE full_name LIKE ? 
        OR patient_id LIKE ?
        OR nurse_name LIKE ?
    ''', (search_pattern, search_pattern, search_pattern))
    
    total = cursor.fetchone()[0]
    
    # Get paginated results
    cursor.execute('''
        SELECT * FROM records 
        WHERE full_name LIKE ? 
        OR patient_id LIKE ?
        OR nurse_name LIKE ?
        ORDER BY date_of_visit DESC, time_of_visit DESC
        LIMIT ? OFFSET ?
    ''', (search_pattern, search_pattern, search_pattern, per_page, offset))
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        'items': records,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }

def get_all_records(page=1, per_page=20):
    """Get all health records with pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    # Count total records
    cursor.execute('SELECT COUNT(*) FROM records')
    total = cursor.fetchone()[0]
    
    # Get paginated results
    cursor.execute('''
        SELECT * FROM records 
        ORDER BY date_of_visit DESC, time_of_visit DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        'items': records,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }
