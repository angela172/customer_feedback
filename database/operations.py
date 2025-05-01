import streamlit as st
from datetime import datetime
import traceback
from database.models import Feedback
from database.connection import get_db_session, init_database_tables

def set_branch_from_url():
    """Set the branch from URL query parameters"""
    query_params = st.query_params
    branch = query_params.get('branch', None)
    if branch:
        st.session_state.form_data['branch'] = branch
    return branch

def save_form_data(form_data):
    """Save form data to the database using SQLAlchemy"""
    try:
        print("Starting save_form_data with SQLAlchemy...")
        
        # Ensure database tables exist
        init_database_tables()
        
        # Get database session
        db_gen = get_db_session()
        session = next(db_gen)
        
        # Debug print - console only
        print(f"Form data: {form_data}")
        
        # Handle potential NPS value conversion
        nps_value = None
        if 'nps' in form_data:
            try:
                nps_value = int(form_data['nps']) if form_data['nps'] is not None else None
                print(f"Converted NPS value: {nps_value}")
            except (ValueError, TypeError):
                print(f"Invalid NPS value: {form_data.get('nps')}")
                nps_value = None
        
        # Create a new Feedback record
        print("Creating Feedback record object...")
        feedback_record = Feedback(
            timestamp=datetime.now(),
            name=str(form_data.get('name', '')),
            email=str(form_data.get('email', '')),
            phone=str(form_data.get('phone', '')),
            language=str(form_data.get('language', '')),
            nps=nps_value,
            first_visit=str(form_data.get('first_visit', '')),
            satisfaction=str(form_data.get('satisfaction', '')),
            satisfaction_reason=str(form_data.get('satisfaction_reason', '')),
            dissatisfaction_reason=str(form_data.get('dissatisfaction_reason', '')),
            dissatisfaction_reason_text=str(form_data.get('specific_reason', '')),
            feedback=str(form_data.get('feedback', '')),
            branch=str(form_data.get('branch', '')),
        )
        
        # Display the record we're about to save - console only
        print("About to save record:", vars(feedback_record))
        
        # Add and commit the record
        print("Adding record to session...")
        session.add(feedback_record)
        print("Committing to database...")
        session.commit()
        print("Commit successful!")
        
        # Close the session
        try:
            next(db_gen)  # This will trigger the finally block in get_db_session
        except StopIteration:
            pass
            
        return True
    except Exception as e:
        print(f"Error in save_form_data: {str(e)}")
        # Print more detail about the error - console only
        error_trace = traceback.format_exc()
        print("Error details:", error_trace)
        return False

def phone_exists_in_database(phone_number):
    """Check if the phone number already exists in the database using SQLAlchemy"""
    try:
        db_gen = get_db_session()
        session = next(db_gen)
        
        # Query for existing phone number
        existing_record = session.query(Feedback).filter(Feedback.phone == phone_number).first()
        
        # Close the session
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        # Return True if the phone number already exists
        return existing_record is not None
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            print(f"Error checking phone number in database: {str(e)}")
        return False

def get_phone_occurrence_count(phone_number):
    """Check how many times a phone number appears in the database using SQLAlchemy"""
    try:
        db_gen = get_db_session()
        session = next(db_gen)
        
        # Query for phone number occurrences
        count = session.query(Feedback).filter(Feedback.phone == phone_number).count()
        
        # Close the session
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        # Return the count
        return count
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            print(f"Error checking phone number count in database: {str(e)}")
        return 0

# Initialize form data if not exists
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
        
