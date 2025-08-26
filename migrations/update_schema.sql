-- Migration to update database schema with new fields
BEGIN TRANSACTION;

-- Create a new table with all the required fields
CREATE TABLE IF NOT EXISTS new_records (
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
    temperature REAL,  -- in Fahrenheit
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
);

-- Copy existing data to the new table with field mappings
INSERT INTO new_records (
    id, patient_id, full_name, date_of_birth, age, gender, grade_level,
    date_of_visit, time_of_visit, nurse_name, visit_reason_category, visit_details,
    temperature, heart_rate, respiratory_rate, oxygen_saturation,
    blood_pressure_systolic, blood_pressure_diastolic, notes, created_at
) 
SELECT 
    id, patient_id, full_name, date_of_birth, age, gender, grade_level,
    date_of_visit, time_of_visit, nurse_name, visit_reason as visit_reason_category, NULL as visit_details,
    ((temperature - 32.0) * 5.0/9.0) as temperature, pulse as heart_rate, NULL as respiratory_rate, NULL as oxygen_saturation,
    NULL as blood_pressure_systolic, NULL as blood_pressure_diastolic, notes, created_at
FROM records;

-- Drop the old table and rename the new one
DROP TABLE records;
ALTER TABLE new_records RENAME TO records;

-- Create indexes for better query performance
CREATE INDEX idx_patient_id ON records(patient_id);
CREATE INDEX idx_full_name ON records(full_name);
CREATE INDEX idx_date_of_visit ON records(date_of_visit);
CREATE INDEX idx_visit_reason_category ON records(visit_reason_category);

COMMIT;
