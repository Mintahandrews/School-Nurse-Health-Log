from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, 
    current_app, send_file
)
import sqlite3
import os
from datetime import datetime
import re
import tempfile
import pandas as pd
from ..models.db import get_db_connection, generate_patient_id
from ..forms.forms import RecordForm, SearchForm, ImportForm
from ..utils.excel_utils import initialize_excel_file, export_records_to_excel
import openpyxl

# Create Blueprint
main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    """Home page displaying all records"""
    form = SearchForm()
    conn = get_db_connection()
    
    # If it's a search request, filter the records
    if form.validate_on_submit() or request.args.get('search_term'):
        search_term = form.search_term.data or request.args.get('search_term', '')
        form.search_term.data = search_term
        
        search_pattern = f"%{search_term}%"
        # Use SELECT * to be compatible with older SQLite schemas
        rows = conn.execute(
            '''SELECT * FROM records 
               WHERE full_name LIKE ? OR patient_id LIKE ? OR nurse_name LIKE ?
               ORDER BY date_of_visit DESC, time_of_visit DESC''',
            (search_pattern, search_pattern, search_pattern)
        ).fetchall()
        # Normalize visit_reason key for templates
        records = []
        for r in rows:
            d = dict(r)
            d['visit_reason'] = d.get('visit_reason') or d.get('visit_reason_category')
            records.append(d)
    else:
        # Default: get all records, normalize visit_reason
        rows = conn.execute('''
            SELECT * FROM records 
            ORDER BY date_of_visit DESC, time_of_visit DESC
        ''').fetchall()
        records = []
        for r in rows:
            d = dict(r)
            d['visit_reason'] = d.get('visit_reason') or d.get('visit_reason_category')
            records.append(d)
    
    conn.close()
    return render_template('index.html', records=records, form=form, title="School Nurse Health Log")

@main.route('/search', methods=['GET', 'POST'])
def search():
    """Search for records"""
    form = SearchForm()
    records = []
    
    if form.validate_on_submit() or request.args.get('search_term'):
        search_term = form.search_term.data or request.args.get('search_term', '')
        form.search_term.data = search_term
        
        conn = get_db_connection()
        search_pattern = f"%{search_term}%"
        rows = conn.execute(
            '''SELECT * FROM records 
               WHERE full_name LIKE ? OR patient_id LIKE ? OR nurse_name LIKE ?
               ORDER BY date_of_visit DESC, time_of_visit DESC''', 
            (search_pattern, search_pattern, search_pattern)
        ).fetchall()
        conn.close()
        # Normalize visit_reason for template compatibility
        for r in rows:
            d = dict(r)
            d['visit_reason'] = d.get('visit_reason') or d.get('visit_reason_category')
            records.append(d)
    
    return render_template('search.html', form=form, records=records, title="Search Records")

@main.route('/add', methods=['GET', 'POST'])
def add_record():
    """Add a new health record"""
    form = RecordForm()
    
    if form.validate_on_submit():
        conn = get_db_connection()
        patient_id = generate_patient_id()
        
        # Format date and time objects to strings
        date_of_birth = form.date_of_birth.data.strftime('%Y-%m-%d') if form.date_of_birth.data else None
        date_of_visit = form.date_of_visit.data.strftime('%Y-%m-%d')
        time_of_visit = form.time_of_visit.data.strftime('%H:%M')
        
        conn.execute(
            '''INSERT INTO records 
               (patient_id, full_name, date_of_birth, age, gender, grade_level,
                date_of_visit, time_of_visit, nurse_name, visit_reason_category, visit_details,
                temperature, heart_rate, respiratory_rate, oxygen_saturation,
                blood_pressure_systolic, blood_pressure_diastolic,
                height, weight, bmi, pain_scale, pain_location,
                notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                patient_id,
                form.full_name.data,
                date_of_birth,
                form.age.data,
                form.gender.data,
                form.grade_level.data,
                date_of_visit,
                time_of_visit,
                form.nurse_name.data,
                (form.visit_reason.data or form.visit_reason_category.data),
                form.visit_details.data,
                form.temperature.data,
                form.heart_rate.data,
                form.respiratory_rate.data,
                form.oxygen_saturation.data,
                form.blood_pressure_systolic.data,
                form.blood_pressure_diastolic.data,
                form.height.data,
                form.weight.data,
                form.bmi.data,
                (form.pain_level.data if hasattr(form, 'pain_level') else form.pain_scale.data),
                form.pain_location.data,
                form.notes.data,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )
        conn.commit()
        conn.close()
        
        flash(f'Record for {form.full_name.data} added successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('record_form.html', form=form, title="Add Health Record")

@main.route('/edit/<patient_id>', methods=['GET', 'POST'])
def edit_record(patient_id):
    """Edit an existing health record"""
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM records WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    
    if record is None:
        flash('Record not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Convert sqlite3.Row to dict for safe .get() access
    record = dict(record)

    form = RecordForm()
    
    if request.method == 'GET':
        # Populate form with existing data
        form.full_name.data = record['full_name']
        if record['date_of_birth']:
            try:
                form.date_of_birth.data = datetime.strptime(record['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                form.date_of_birth.data = None
        form.age.data = record['age']
        form.gender.data = record['gender']
        form.grade_level.data = record['grade_level']
        form.date_of_visit.data = datetime.strptime(record['date_of_visit'], '%Y-%m-%d').date()
        form.time_of_visit.data = datetime.strptime(record['time_of_visit'], '%H:%M').time()
        form.nurse_name.data = record['nurse_name']
        form.visit_reason.data = record.get('visit_reason_category') or record.get('visit_reason')
        form.visit_details.data = record.get('visit_details', '')
        form.temperature.data = record.get('temperature')
        form.heart_rate.data = record.get('heart_rate')
        form.respiratory_rate.data = record.get('respiratory_rate')
        form.oxygen_saturation.data = record.get('oxygen_saturation')
        form.blood_pressure_systolic.data = record.get('blood_pressure_systolic')
        form.blood_pressure_diastolic.data = record.get('blood_pressure_diastolic')
        form.height.data = record.get('height')
        form.weight.data = record.get('weight')
        form.bmi.data = record.get('bmi')
        if hasattr(form, 'pain_scale'):
            form.pain_scale.data = record.get('pain_scale')
        if hasattr(form, 'pain_level') and form.pain_level.data is None:
            form.pain_level.data = record.get('pain_level')
        form.pain_location.data = record.get('pain_location')
        form.notes.data = record.get('notes')
    
    if form.validate_on_submit():
        # Format date and time objects to strings
        date_of_birth = form.date_of_birth.data.strftime('%Y-%m-%d') if form.date_of_birth.data else None
        date_of_visit = form.date_of_visit.data.strftime('%Y-%m-%d')
        time_of_visit = form.time_of_visit.data.strftime('%H:%M')
        
        conn = get_db_connection()
        conn.execute(
            '''UPDATE records SET 
               full_name = ?, date_of_birth = ?, age = ?, gender = ?, grade_level = ?, 
               date_of_visit = ?, time_of_visit = ?, nurse_name = ?, visit_reason_category = ?, 
               visit_details = ?, temperature = ?, heart_rate = ?, respiratory_rate = ?, oxygen_saturation = ?,
               blood_pressure_systolic = ?, blood_pressure_diastolic = ?,
               height = ?, weight = ?, bmi = ?, pain_scale = ?, pain_location = ?,
               notes = ? 
               WHERE patient_id = ?''',
            (
                form.full_name.data, date_of_birth, form.age.data, form.gender.data, 
                form.grade_level.data, date_of_visit, time_of_visit, form.nurse_name.data,
                (form.visit_reason.data or form.visit_reason_category.data), form.visit_details.data, form.temperature.data,
                form.heart_rate.data, form.respiratory_rate.data, form.oxygen_saturation.data,
                form.blood_pressure_systolic.data, form.blood_pressure_diastolic.data,
                form.height.data, form.weight.data, form.bmi.data,
                (form.pain_level.data if hasattr(form, 'pain_level') else form.pain_scale.data), form.pain_location.data,
                form.notes.data, patient_id
            )
        )
        conn.commit()
        conn.close()
        
        flash(f'Record for {form.full_name.data} updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('record_form.html', form=form, title="Edit Health Record", record=record)

@main.route('/delete/<patient_id>', methods=['POST'])
def delete_record(patient_id):
    """Delete a health record"""
    conn = get_db_connection()
    record = conn.execute('SELECT full_name FROM records WHERE patient_id = ?', (patient_id,)).fetchone()
    
    if record:
        conn.execute('DELETE FROM records WHERE patient_id = ?', (patient_id,))
        conn.commit()
        flash(f'Record for {record["full_name"]} deleted successfully!', 'success')
    else:
        flash('Record not found', 'danger')
    
    conn.close()
    return redirect(url_for('main.index'))

@main.route('/view/<patient_id>')
def view_record(patient_id):
    """View details of a health record"""
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM records WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    
    if record is None:
        flash('Record not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Normalize to dict and ensure template-friendly keys
    record = dict(record)
    record['visit_reason'] = record.get('visit_reason') or record.get('visit_reason_category')
    return render_template('view_record.html', record=record, title="View Health Record")

@main.route('/export')
def export_to_excel():
    """Export all health records to Excel"""
    try:
        conn = get_db_connection()
        records = conn.execute('SELECT * FROM records ORDER BY date_of_visit DESC, time_of_visit DESC').fetchall()
        conn.close()
        
        if not records:
            flash('No records to export', 'warning')
            return redirect(url_for('main.index'))
        
        # Ensure we pass dictionaries to the Excel exporter (sqlite3.Row doesn't have .get)
        records = [dict(r) for r in records]
        
        # Create a temporary file to store the Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            filename = tmp.name
        
        # Use our utility function to export records
        export_records_to_excel(records, filename)
        
        # Send the file to the user
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"nurse_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.exception("Export failed")
        flash(f"Export failed: {str(e)}", 'danger')
        return redirect(url_for('main.index'))

@main.route('/import', methods=['GET', 'POST'])
def import_from_excel():
    """Import health records from Excel"""
    form = ImportForm()
    
    if form.validate_on_submit():
        try:
            # Save the uploaded file temporarily
            excel_file = request.files[form.excel_file.name]
            filename = tempfile.mktemp(suffix='.xlsx')
            excel_file.save(filename)
            
            # Read Excel into DataFrame
            df = pd.read_excel(filename, header=0 if form.has_headers.data else None)
            
            # Clean up temporary file
            os.unlink(filename)
            
            # Process DataFrame
            if not form.has_headers.data:
                # Create default column names if no headers
                df.columns = [f'col_{i}' for i in range(len(df.columns))]
            
            # Map DataFrame columns to database fields
            required_cols = ['full_name', 'date_of_visit', 'time_of_visit', 'nurse_name']
            db_columns = {
                'patient_id': None,
                'full_name': None,
                'date_of_birth': None,
                'age': None,
                'gender': None,
                'grade_level': None,
                'date_of_visit': None,
                'time_of_visit': None,
                'nurse_name': None,
                # reason fields (support legacy and new)
                'visit_reason': None,
                'visit_reason_category': None,
                'visit_details': None,
                # vitals (support legacy pulse and new heart_rate)
                'temperature': None,
                'pulse': None,
                'heart_rate': None,
                'blood_pressure': None,  # combined like 120/80
                # free text
                'notes': None
            }
            
            # Check if required columns exist in DataFrame
            missing_cols = []
            for col in df.columns:
                # Normalize column name for matching
                col_name = str(col).strip().lower().replace(' ', '_')
                
                # Map to database field if possible
                for db_col in db_columns:
                    if db_col in col_name or col_name in db_col:
                        db_columns[db_col] = col
                        break
            
            # Check for missing required columns
            for req_col in required_cols:
                if db_columns[req_col] is None:
                    missing_cols.append(req_col)
            
            if missing_cols:
                flash(f'Missing required columns: {", ".join(missing_cols)}', 'danger')
                return render_template('import.html', form=form, title="Import Records")
            
            # Connect to database
            conn = get_db_connection()
            
            # Process each row and insert into database
            success_count = 0
            error_count = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Generate a patient ID if not provided
                    patient_id = str(row.get(db_columns['patient_id'], '')).strip() or generate_patient_id()
                    
                    # Format date fields
                    date_of_birth = None
                    if db_columns['date_of_birth'] is not None:
                        try:
                            dob = pd.to_datetime(row[db_columns['date_of_birth']])
                            date_of_birth = dob.strftime('%Y-%m-%d')
                        except:
                            date_of_birth = None
                    
                    # Format visit date
                    try:
                        visit_date = pd.to_datetime(row[db_columns['date_of_visit']])
                        date_of_visit = visit_date.strftime('%Y-%m-%d')
                    except:
                        error_count += 1
                        errors.append(f"Row {success_count + error_count}: Invalid date format")
                        continue
                    
                    # Format visit time
                    try:
                        time_value = row[db_columns['time_of_visit']]
                        if isinstance(time_value, str):
                            # Parse string time
                            time_parts = time_value.strip().split(':')
                            if len(time_parts) >= 2:
                                time_of_visit = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}"
                            else:
                                time_of_visit = "00:00"
                        else:
                            # Try to handle datetime objects
                            try:
                                visit_time = pd.to_datetime(time_value)
                                time_of_visit = visit_time.strftime('%H:%M')
                            except:
                                time_of_visit = "00:00"
                    except:
                        time_of_visit = "00:00"
                    
                    # Extract other fields
                    full_name = str(row[db_columns['full_name']]).strip()
                    age = int(row[db_columns['age']]) if db_columns['age'] is not None and pd.notna(row[db_columns['age']]) else None
                    gender = str(row[db_columns['gender']]) if db_columns['gender'] is not None and pd.notna(row[db_columns['gender']]) else None
                    grade_level = str(row[db_columns['grade_level']]) if db_columns['grade_level'] is not None and pd.notna(row[db_columns['grade_level']]) else None
                    nurse_name = str(row[db_columns['nurse_name']]).strip() if db_columns['nurse_name'] is not None else "Unknown"
                    # Visit reason (prefer explicit visit_reason_category if present)
                    visit_reason = None
                    if db_columns['visit_reason_category'] is not None and pd.notna(row[db_columns['visit_reason_category']]):
                        visit_reason = str(row[db_columns['visit_reason_category']])
                    elif db_columns['visit_reason'] is not None and pd.notna(row[db_columns['visit_reason']]):
                        visit_reason = str(row[db_columns['visit_reason']])
                    visit_details = str(row[db_columns['visit_details']]) if db_columns['visit_details'] is not None and pd.notna(row[db_columns['visit_details']]) else None
                    temperature = float(row[db_columns['temperature']]) if db_columns['temperature'] is not None and pd.notna(row[db_columns['temperature']]) else None
                    # Heart rate from either 'heart_rate' or legacy 'pulse'
                    hr = None
                    if db_columns['heart_rate'] is not None and pd.notna(row[db_columns['heart_rate']]):
                        try:
                            hr = int(row[db_columns['heart_rate']])
                        except:
                            hr = None
                    if hr is None and db_columns['pulse'] is not None and pd.notna(row[db_columns['pulse']]):
                        try:
                            hr = int(row[db_columns['pulse']])
                        except:
                            hr = None
                    # Blood pressure: parse combined string like "120/80"
                    bp_sys = None
                    bp_dia = None
                    if db_columns['blood_pressure'] is not None and pd.notna(row[db_columns['blood_pressure']]):
                        try:
                            bp_text = str(row[db_columns['blood_pressure']])
                            parts = [p for p in re.split(r"[^0-9]", bp_text) if p.strip()]
                            if len(parts) >= 2:
                                bp_sys = int(parts[0])
                                bp_dia = int(parts[1])
                        except:
                            bp_sys = None
                            bp_dia = None
                    notes = str(row[db_columns['notes']]) if db_columns['notes'] is not None and pd.notna(row[db_columns['notes']]) else None
                    
                    # Insert record into database
                    conn.execute(
                        '''INSERT OR REPLACE INTO records 
                           (patient_id, full_name, date_of_birth, age, gender, grade_level, 
                            date_of_visit, time_of_visit, nurse_name, visit_reason_category, visit_details,
                            temperature, heart_rate, blood_pressure_systolic, blood_pressure_diastolic, notes, created_at) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (patient_id, full_name, date_of_birth, age, gender, grade_level, 
                         date_of_visit, time_of_visit, nurse_name, visit_reason, visit_details,
                         temperature, hr, bp_sys, bp_dia, notes, 
                         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {success_count + error_count}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Show results
            if success_count > 0:
                flash(f'Successfully imported {success_count} records', 'success')
            if error_count > 0:
                flash(f'Failed to import {error_count} records', 'warning')
                for error in errors[:10]:  # Show first 10 errors
                    flash(error, 'danger')
                if len(errors) > 10:
                    flash(f'... and {len(errors) - 10} more errors', 'danger')
            
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'Error importing Excel file: {str(e)}', 'danger')
    
    return render_template('import.html', form=form, title="Import Records")
