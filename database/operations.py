import streamlit as st
from datetime import datetime
import traceback
from database.models import Feedback
from database.connection import get_db, init_database_tables
from sqlalchemy.orm import Session

def set_branch_from_url():
    """Set the branch from URL query parameters"""
    try:
        # First try to get branch from query params
        branch = st.query_params.get('branch', None)
        print(f"Branch from query params: {branch}")  # Debug print
        
        # If no branch in query params, try to extract from hostname
        if not branch:
            hostname = st.query_params.get("_st_url", "")
            print(f"Hostname from URL: {hostname}")  # Debug print
            
            if hostname:
                # Extract subdomain from hostname
                # Format: https://ajmalfeedback-dubai.streamlit.app
                parts = hostname.split("//")[1].split(".")
                if len(parts) >= 2 and "ajmalfeedback-" in parts[0]:
                    branch = parts[0].replace("ajmalfeedback-", "")
                    print(f"Extracted branch from hostname: {branch}")  # Debug print
        
        # If still no branch, use a default
        if not branch:
            branch = "dubai"  # Change this to your default branch
            print(f"Using default branch: {branch}")  # Debug print
        
        # Set the branch in form data
        if branch:
            st.session_state.form_data['branch'] = branch
            print(f"Branch set to: {branch}")  # Debug print
        
        return branch
        
    except Exception as e:
        print(f"Error setting branch from URL: {str(e)}")
        return None

def save_form_data(form_data: dict) -> bool:
    """Save form data to the database"""
    print("Starting save_form_data function...")  # Debug print
    print(f"Form data to save: {form_data}")  # Debug print
    
    # Validate required fields
    required_fields = ['name', 'email', 'phone', 'branch']
    for field in required_fields:
        if not form_data.get(field):
            print(f"Missing required field: {field}")
            return False
    
    # Validate email format
    if '@' not in form_data['email'] or not form_data['email'].endswith('.com'):
        print("Invalid email format")
        return False
    
    # Ensure database tables are initialized
    if not init_database_tables():
        print("Failed to initialize database tables")
        return False
    
    db = None
    try:
        # Get database session
        db = get_db()
        
        # Create new feedback entry with timestamp
        feedback_data = form_data.copy()
        feedback_data['timestamp'] = datetime.now()
        
        # Create new feedback entry
        feedback = Feedback(**feedback_data)
        
        # Add to session and commit
        db.add(feedback)
        db.commit()
        print("Form data saved successfully")  # Debug print
        return True
        
    except Exception as e:
        print(f"Error saving form data: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
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
        
