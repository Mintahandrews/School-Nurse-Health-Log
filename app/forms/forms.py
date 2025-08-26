from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
    StringField, DateField, TimeField, SelectField, TextAreaField, 
    SubmitField, BooleanField, IntegerField, FloatField, DecimalField
)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email, URL, AnyOf
from datetime import datetime, date

# Custom validators
def validate_date_not_future(form, field):
    if field.data and field.data > date.today():
        raise ValidationError('Date cannot be in the future.')

def validate_time_not_future(form, field):
    if field.data and field.data > datetime.now().time() and form.date_of_visit.data == date.today():
        raise ValidationError('Time cannot be in the future.')

class RecordForm(FlaskForm):
    """Form for adding and editing health records with comprehensive fields"""
    
    # ===== Student Demographics =====
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=0, max=30)])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Non-binary', 'Non-binary'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say')
    ], validators=[Optional()])
    grade_level = SelectField('Grade/Year Level', choices=[
        ('', 'Select Grade'),
        ('Pre-K', 'Pre-K'),
        ('K', 'Kindergarten'),
        *[(str(i), f'Grade {i}') for i in range(1, 13)],
        ('College', 'College')
    ], validators=[Optional()])
    
    # ===== Contact Information =====
    parent_primary_name = StringField("Parent/Guardian's Name", validators=[Optional(), Length(max=100)])
    parent_primary_phone = StringField("Parent/Guardian's Phone", validators=[Optional(), Length(max=20)])
    emergency_contact_name = StringField("Emergency Contact Name", validators=[Optional(), Length(max=100)])
    emergency_contact_phone = StringField("Emergency Contact Phone", validators=[Optional(), Length(max=20)])
    
    # ===== Visit Information =====
    academic_year = StringField('Academic Year', validators=[Optional()], 
                              default=f"{datetime.now().year}-{datetime.now().year + 1}")
    academic_term = SelectField('Academic Term', choices=[
        ('', 'Select Term'),
        ('Fall', 'Fall'),
        ('Winter', 'Winter'),
        ('Spring', 'Spring'),
        ('Summer', 'Summer')
    ], validators=[Optional()])
    date_of_visit = DateField('Date of Visit', validators=[DataRequired(), validate_date_not_future], 
                             format='%Y-%m-%d', default=date.today)
    time_of_visit = TimeField('Time of Visit', validators=[DataRequired(), validate_time_not_future], 
                             format='%H:%M', default=datetime.now().time)
    brought_in_by = SelectField('Brought In By', choices=[
        ('', 'Select Option'),
        ('Teacher', 'Teacher'),
        ('Staff', 'Staff'),
        ('Self', 'Self'),
        ('Parent', 'Parent'),
        ('Other', 'Other')
    ], validators=[Optional()])
    nurse_name = StringField('Nurse Name', validators=[DataRequired(), Length(max=100)])
    
    # Standardized to use visit_reason_category only (removed duplicate visit_reason)
    visit_reason_category = SelectField('Visit Reason', choices=[
        ('', 'Select Reason'),
        ('Illness', 'Illness'),
        ('Injury', 'Injury'),
        ('Medication', 'Medication'),
        ('Routine Check', 'Routine Check'),
        ('Follow-up', 'Follow-up'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    
    severity_level = SelectField('Severity Level', choices=[
        ('', 'Select Severity'),
        ('Mild', 'Mild'),
        ('Moderate', 'Moderate'),
        ('Severe', 'Severe'),
        ('Critical', 'Critical')
    ], validators=[Optional()])
    
    # ===== Vital Signs =====
    # Standardized to use heart_rate instead of pulse
    temperature = DecimalField('Temperature (°F)', places=1, validators=[
        Optional(), 
        NumberRange(min=90, max=110, message='Temperature must be between 90-110°F')
    ])
    heart_rate = IntegerField('Heart Rate (bpm)', validators=[
        Optional(), 
        NumberRange(min=30, max=250, message='Heart rate must be between 30-250 bpm')
    ])
    respiratory_rate = IntegerField('Respiratory Rate (breaths/min)', validators=[
        Optional(), 
        NumberRange(min=5, max=60, message='Respiratory rate must be between 5-60 breaths/min')
    ])
    oxygen_saturation = IntegerField('Oxygen Saturation (%)', validators=[
        Optional(), 
        NumberRange(min=70, max=100, message='Oxygen saturation must be between 70-100%')
    ])
    # Split blood pressure into systolic and diastolic
    blood_pressure_systolic = IntegerField('Systolic BP', validators=[
        Optional(),
        NumberRange(min=70, max=200, message='Systolic BP must be between 70-200 mmHg')
    ])
    blood_pressure_diastolic = IntegerField('Diastolic BP', validators=[
        Optional(),
        NumberRange(min=40, max=120, message='Diastolic BP must be between 40-120 mmHg')
    ])
    
    # Added new vital sign fields
    height = DecimalField('Height (in)', places=1, validators=[
        Optional(),
        NumberRange(min=20, max=100, message='Height must be between 20-100 inches')
    ])
    weight = DecimalField('Weight (lbs)', places=1, validators=[
        Optional(),
        NumberRange(min=10, max=1000, message='Weight must be between 10-1000 lbs')
    ])
    bmi = DecimalField('BMI (kg/m²)', places=1, validators=[
        Optional(),
        NumberRange(min=10, max=60, message='BMI must be between 10-60')
    ])
    pain_scale = IntegerField('Pain Scale (0-10)', validators=[
        Optional(),
        NumberRange(min=0, max=10, message='Pain scale must be between 0-10')
    ])
    pain_location = StringField('Pain Location', validators=[Optional(), Length(max=100)])
    
    # ===== Presenting Complaints =====
    presenting_complaints = SelectField('Presenting Complaint(s)', choices=[
        ('', 'Select Complaint'),
        ('Headache', 'Headache'),
        ('Fever', 'Fever'),
        ('Stomach ache', 'Stomach ache'),
        ('Nausea/vomiting', 'Nausea/vomiting'),
        ('Sore throat', 'Sore throat'),
        ('Cold/Cough', 'Cold/Cough'),
        ('Wound/Injury', 'Wound/Injury'),
        ('Sprain', 'Sprain'),
        ('Eye pain', 'Eye pain'),
        ('Ear pain', 'Ear pain'),
        ('Tooth/gum ache', 'Tooth/gum ache'),
        ('Menstrual cramps', 'Menstrual cramps'),
        ('Other', 'Other')
    ], validators=[Optional()])
    other_complaint_details = TextAreaField('Other Complaint Details', validators=[Optional()])
    complaint_background = TextAreaField('Background to Presenting Complaint(s)', validators=[Optional()])
    
    # ===== Medical History =====
    past_medical_history = TextAreaField('Past Medical History', validators=[Optional()])
    known_allergies = TextAreaField('Known Allergies', validators=[Optional()])
    current_medications = TextAreaField('Current Medications', validators=[Optional()])
    # Standardized to use special_medical_needs
    special_medical_needs = BooleanField('Special Medical Needs', default=False)
    chronic_conditions = TextAreaField('Chronic Conditions', validators=[Optional()])
    
    # ===== Assessment & Care =====
    nurse_observations = TextAreaField('Nurse Observations', validators=[Optional()])
    interventions_provided = TextAreaField('Interventions Provided', validators=[Optional()])
    medications_administered = TextAreaField('Medications Administered', validators=[Optional()])
    
    next_steps = SelectField('Next Step(s)', choices=[
        ('', 'Select Next Step'),
        ('Return to class', 'Return to class'),
        ('Admit to sick bay', 'Admit to sick bay'),
        ('Send home', 'Send home'),
        ('Refer to doctor', 'Refer to doctor'),
        ('Call emergency services', 'Call emergency services'),
        ('Follow-up required', 'Follow-up required'),
        ('Other', 'Other')
    ], validators=[Optional()])
    
    other_next_step_details = TextAreaField('Other Next Step Details', validators=[Optional()])
    referral_type = StringField('Referral Type (if applicable)', validators=[Optional()])
    follow_up_date = DateField('Follow-up Date', validators=[Optional()], format='%Y-%m-%d')
    
    # ===== Admission to Sick Bay =====
    admission_date = DateField('Admission Date', validators=[Optional()], format='%Y-%m-%d')
    admission_time = TimeField('Admission Time', validators=[Optional()], format='%H:%M')
    condition_on_admission = TextAreaField("Student's Condition on Admission", validators=[Optional()])
    plan_of_care = TextAreaField('Plan of Care', validators=[Optional()])
    
    # ===== Discharge Information =====
    discharge_time = TimeField('Discharge Time', validators=[Optional()], format='%H:%M')
    condition_at_discharge = TextAreaField("Student's Condition at Discharge", validators=[Optional()])
    discharge_instructions = TextAreaField('Discharge Instructions', validators=[Optional()])
    return_to_class_time = TimeField('Return to Class Time', validators=[Optional()], format='%H:%M')
    
    parent_notified = BooleanField('Parent Notified', default=False)
    parent_notification_time = TimeField('Parent Notification Time', validators=[Optional()], format='%H:%M')
    incident_report_required = BooleanField('Incident Report Required', default=False)
    
    # ===== General Notes =====
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    
    # Submit button
    submit = SubmitField('Save Record', render_kw={"class": "btn btn-primary"})

class SearchForm(FlaskForm):
    """Form for searching records"""
    search_term = StringField('Search by Name, ID, or Nurse', validators=[DataRequired()])
    submit = SubmitField('Search')

class ImportForm(FlaskForm):
    """Form for importing records from Excel"""
    excel_file = FileField('Excel File', validators=[DataRequired()])
    has_headers = BooleanField('First row contains headers', default=True)
    submit = SubmitField('Import Records')
