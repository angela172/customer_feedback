import streamlit as st
from datetime import datetime
import traceback
from database.models import Feedback
from database.connection import get_db, init_database_tables
from sqlalchemy.orm import Session

def set_branch_from_url():
    """Set the branch from URL query parameters"""
    query_params = st.query_params
    branch = query_params.get('branch', None)
    if branch:
        st.session_state.form_data['branch'] = branch
    return branch

def save_form_data(form_data: dict) -> bool:
    """Save form data to the database"""
    print("Starting save_form_data function...")  # Debug print
    print(f"Form data to save: {form_data}")  # Debug print
    
    # Ensure database tables are initialized
    if not init_database_tables():
        print("Failed to initialize database tables")
        return False
    
    db = None
    try:
        # Get database session
        db = get_db()
        
        # Create new feedback entry
        feedback = Feedback(**form_data)
        
        # Add to session and commit
        db.add(feedback)
        db.commit()
        print("Form data saved successfully")  # Debug print
        return True
        
    except Exception as e:
        print(f"Error saving form data: {str(e)}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

def phone_exists_in_database(phone_number):
    """Check if the phone number already exists in the database using SQLAlchemy"""
    try:
        db_gen = get_db()
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
        db_gen = get_db()
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
        
