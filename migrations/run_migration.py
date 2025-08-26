import os
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.models.db import get_db_connection

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cursor.fetchall()]

def run_migration():
    app = create_app()
    
    with app.app_context():
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1) Create new table with the latest schema
            cur.execute("""
                CREATE TABLE IF NOT EXISTS new_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE,
                    full_name TEXT NOT NULL,
                    date_of_birth TEXT,
                    age INTEGER,
                    gender TEXT,
                    grade_level TEXT,
                    parent_primary_name TEXT,
                    parent_primary_phone TEXT,
                    emergency_contact_name TEXT,
                    emergency_contact_phone TEXT,
                    academic_year TEXT,
                    academic_term TEXT,
                    date_of_visit TEXT NOT NULL,
                    time_of_visit TEXT NOT NULL,
                    brought_in_by TEXT,
                    nurse_name TEXT NOT NULL,
                    visit_reason_category TEXT,
                    severity_level TEXT,
                    visit_details TEXT,
                    temperature REAL,
                    heart_rate INTEGER,
                    respiratory_rate INTEGER,
                    oxygen_saturation REAL,
                    blood_pressure_systolic INTEGER,
                    blood_pressure_diastolic INTEGER,
                    height REAL,
                    weight REAL,
                    bmi REAL,
                    pain_scale INTEGER,
                    pain_location TEXT,
                    presenting_complaints TEXT,
                    other_complaint_details TEXT,
                    complaint_background TEXT,
                    past_medical_history TEXT,
                    known_allergies TEXT,
                    current_medications TEXT,
                    special_medical_needs BOOLEAN DEFAULT 0,
                    chronic_conditions TEXT,
                    nurse_observations TEXT,
                    interventions_provided TEXT,
                    medications_administered TEXT,
                    next_steps TEXT,
                    other_next_step_details TEXT,
                    referral_type TEXT,
                    follow_up_date TEXT,
                    admission_date TEXT,
                    admission_time TEXT,
                    condition_on_admission TEXT,
                    plan_of_care TEXT,
                    discharge_time TEXT,
                    condition_at_discharge TEXT,
                    discharge_instructions TEXT,
                    return_to_class_time TEXT,
                    parent_notified BOOLEAN DEFAULT 0,
                    parent_notification_time TEXT,
                    incident_report_required BOOLEAN DEFAULT 0,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # 2) Detect existing columns in old table
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records'")
            if not cur.fetchone():
                # Nothing to migrate, just rename new table to records
                cur.execute("ALTER TABLE new_records RENAME TO records")
                conn.commit()
                print("Initialized new records table.")
                return

            cur.execute("PRAGMA table_info(records)")
            old_cols = {row[1] for row in cur.fetchall()}

            # Helpers for safe expressions
            def src(col):
                return col if col in old_cols else None

            def expr_or_null(expression_if_available):
                return expression_if_available if expression_if_available else 'NULL'

            # Build the INSERT mapping dynamically
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            mappings = [
                ('id', expr_or_null(src('id'))),
                ('patient_id', expr_or_null(src('patient_id'))),
                ('full_name', expr_or_null(src('full_name'))),
                ('date_of_birth', expr_or_null(src('date_of_birth'))),
                ('age', expr_or_null(src('age'))),
                ('gender', expr_or_null(src('gender'))),
                ('grade_level', expr_or_null(src('grade_level'))),
                ('parent_primary_name', expr_or_null(src('parent_primary_name'))),
                ('parent_primary_phone', expr_or_null(src('parent_primary_phone'))),
                ('emergency_contact_name', expr_or_null(src('emergency_contact_name'))),
                ('emergency_contact_phone', expr_or_null(src('emergency_contact_phone'))),
                ('academic_year', expr_or_null(src('academic_year'))),
                ('academic_term', expr_or_null(src('academic_term'))),
                ('date_of_visit', expr_or_null(src('date_of_visit'))),
                ('time_of_visit', expr_or_null(src('time_of_visit'))),
                ('brought_in_by', expr_or_null(src('brought_in_by'))),
                ('nurse_name', expr_or_null(src('nurse_name'))),
                # visit_reason_category: prefer visit_reason_category, else visit_reason
                ('visit_reason_category', (
                    'visit_reason_category' if 'visit_reason_category' in old_cols else (
                        'visit_reason' if 'visit_reason' in old_cols else None
                    )
                )),
                ('severity_level', expr_or_null(src('severity_level'))),
                ('visit_details', 'NULL'),
                # temperature: convert F->C if temperature exists
                ('temperature', '((temperature - 32.0) * 5.0/9.0)' if 'temperature' in old_cols else 'NULL'),
                # heart rate: pulse -> heart_rate else existing heart_rate
                ('heart_rate', 'pulse' if 'pulse' in old_cols else ( 'heart_rate' if 'heart_rate' in old_cols else 'NULL')),
                ('respiratory_rate', expr_or_null(src('respiratory_rate'))),
                ('oxygen_saturation', expr_or_null(src('oxygen_saturation'))),
                # split BP not present in legacy; leave NULL
                ('blood_pressure_systolic', 'NULL'),
                ('blood_pressure_diastolic', 'NULL'),
                ('height', expr_or_null(src('height'))),
                ('weight', expr_or_null(src('weight'))),
                ('bmi', expr_or_null(src('bmi'))),
                # pain_scale: prefer pain_scale else pain_level
                ('pain_scale', 'pain_scale' if 'pain_scale' in old_cols else ('pain_level' if 'pain_level' in old_cols else 'NULL')),
                ('pain_location', expr_or_null(src('pain_location'))),
                ('presenting_complaints', expr_or_null(src('presenting_complaints'))),
                ('other_complaint_details', expr_or_null(src('other_complaint_details'))),
                ('complaint_background', expr_or_null(src('complaint_background'))),
                ('past_medical_history', expr_or_null(src('past_medical_history'))),
                ('known_allergies', expr_or_null(src('known_allergies'))),
                ('current_medications', expr_or_null(src('current_medications'))),
                # special_medical_needs: map from special_needs_flag if present
                ('special_medical_needs', 'special_medical_needs' if 'special_medical_needs' in old_cols else ('special_needs_flag' if 'special_needs_flag' in old_cols else '0')),
                ('chronic_conditions', expr_or_null(src('chronic_conditions'))),
                ('nurse_observations', expr_or_null(src('nurse_observations'))),
                ('interventions_provided', expr_or_null(src('interventions_provided'))),
                ('medications_administered', expr_or_null(src('medications_administered'))),
                ('next_steps', expr_or_null(src('next_steps'))),
                ('other_next_step_details', expr_or_null(src('other_next_step_details'))),
                ('referral_type', expr_or_null(src('referral_type'))),
                ('follow_up_date', expr_or_null(src('follow_up_date'))),
                ('admission_date', expr_or_null(src('admission_date'))),
                ('admission_time', expr_or_null(src('admission_time'))),
                ('condition_on_admission', expr_or_null(src('condition_on_admission'))),
                ('plan_of_care', expr_or_null(src('plan_of_care'))),
                ('discharge_time', expr_or_null(src('discharge_time'))),
                ('condition_at_discharge', expr_or_null(src('condition_at_discharge'))),
                ('discharge_instructions', expr_or_null(src('discharge_instructions'))),
                ('return_to_class_time', expr_or_null(src('return_to_class_time'))),
                ('parent_notified', expr_or_null(src('parent_notified'))),
                ('parent_notification_time', expr_or_null(src('parent_notification_time'))),
                ('incident_report_required', expr_or_null(src('incident_report_required'))),
                ('notes', expr_or_null(src('notes'))),
                ('created_at', expr_or_null(src('created_at'))),
                ('updated_at', f"'{now}'")
            ]

            target_cols = ', '.join(col for col, _ in mappings)
            select_exprs = ', '.join(expr_or_null(expr) if expr not in ('NULL',) else 'NULL' for _, expr in mappings)

            sql = f"""
                INSERT INTO new_records ({target_cols})
                SELECT {select_exprs} FROM records
            """
            cur.execute(sql)

            # 3) Replace old table
            cur.execute('DROP TABLE records')
            cur.execute('ALTER TABLE new_records RENAME TO records')

            # 4) Indexes
            cur.execute('CREATE INDEX IF NOT EXISTS idx_patient_id ON records(patient_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_full_name ON records(full_name)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_date_of_visit ON records(date_of_visit)')

            conn.commit()
            print('Database migration completed successfully!')
        except Exception as e:
            conn.rollback()
            print(f"Error during migration: {str(e)}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    run_migration()
