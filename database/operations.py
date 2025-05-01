import streamlit as st
from datetime import datetime
import traceback
import psycopg2
from database.models import Feedback
from database.connection import get_db_session

# PostgreSQL connection credentials

DB_USER = st.secrets["DB_USER"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]
DB_NAME = st.secrets["DB_NAME"]
DB_HOST = st.secrets["DB_HOST"]
DB_PORT = st.secrets["DB_PORT"]

def set_branch_from_url():
    query_params = st.query_params
    branch = query_params.get('branch', [None])[0]
    if branch:
        st.session_state.form_data['branch'] = branch

def get_direct_connection():
    """Get a direct psycopg2 connection to the database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', True):
            print(f"Error connecting to database: {str(e)}")
        return None

def check_phone_column_exists():
    """Check if the phone column exists in feedback_db table, add it if it doesn't"""
    conn = get_direct_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'feedback_db' AND column_name = 'phone'
            );
        """)
        
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            # Add the column
            cursor.execute("""
                ALTER TABLE feedback_db ADD COLUMN phone VARCHAR(20);
            """)
            conn.commit()
            print("Phone column added successfully to feedback_db table")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', True):
            print(f"Error checking/adding phone column: {str(e)}")
        return False

def check_table_exists():
    """Check if the feedback_db table exists, create it if it doesn't"""
    conn = get_direct_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if table exists in public schema
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'feedback_db'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create the table in public schema
            cursor.execute("""
                CREATE TABLE public.feedback_db (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(20),
                    language VARCHAR(50),
                    nps INTEGER,
                    first_visit VARCHAR(50),
                    satisfaction VARCHAR(50),
                    satisfaction_reason VARCHAR(255),
                    dissatisfaction_reason VARCHAR(255),
                    dissatisfaction_reason_text TEXT,
                    feedback TEXT,
                    branch VARCHAR(255)
                );
            """)
            conn.commit()
            print("Table feedback_db created successfully")
        else:
            # If table exists, check if phone column exists
            check_phone_column_exists()
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', True):
            print(f"Error checking/creating table: {str(e)}")
            traceback.print_exc()  # This will print the full error traceback
        return False

def direct_save_form_data(form_data):
    """Save form data directly using psycopg2"""
    print("Starting direct_save_form_data...")
    
    # Always make sure table exists first
    table_ready = check_table_exists()
    if not table_ready:
        print("Table does not exist or couldn't be created.")
    
    conn = get_direct_connection()
    if not conn:
        print("Failed to get database connection")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Debug print - console only
        print(f"Form data for direct save: {form_data}")
        
        # Handle NPS value
        nps_value = None
        if 'nps' in form_data:
            try:
                nps_value = int(form_data['nps']) if form_data['nps'] is not None else None
                print(f"Converted NPS value: {nps_value}")
            except (ValueError, TypeError):
                print(f"Invalid NPS value: {form_data.get('nps')}")
                nps_value = None
        
        # Print the values we're about to insert - console only
        values = (
            datetime.now(),
            str(form_data.get('name', '')),
            str(form_data.get('email', '')),
            str(form_data.get('phone', '')),
            str(form_data.get('language', '')),
            nps_value,
            str(form_data.get('first_visit', '')),
            str(form_data.get('satisfaction', '')),
            str(form_data.get('satisfaction_reason', '')),
            str(form_data.get('dissatisfaction_reason', '')),
            str(form_data.get('specific_reason', '')),
            str(form_data.get('feedback', '')),
            str(form_data.get('branch', '')),
        )
        
        print(f"Values to insert: {values}")
        
        # Insert the record
        print("Executing SQL INSERT...")
        cursor.execute("""
            INSERT INTO feedback_db (
                timestamp, name, email, phone, language, nps,
                first_visit, satisfaction, satisfaction_reason,
                dissatisfaction_reason, dissatisfaction_reason_text, feedback, branch
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id;
        """, values)
        
        print("SQL executed, getting result...")
        new_id = cursor.fetchone()[0]
        print(f"Got new ID: {new_id}, committing...")
        conn.commit()
        print("Commit successful!")
        
        cursor.close()
        conn.close()
        
        print(f"Record saved with ID: {new_id}")
        
        # Verify the record was saved - console only
        verify_conn = get_direct_connection()
        if verify_conn:
            try:
                verify_cursor = verify_conn.cursor()
                verify_cursor.execute("SELECT * FROM feedback_db WHERE id = %s", (new_id,))
                result = verify_cursor.fetchone()
                if result:
                    print(f"Verified record exists with ID: {new_id}")
                else:
                    print(f"WARNING: Could not verify record with ID: {new_id}")
                verify_cursor.close()
                verify_conn.close()
            except Exception as e:
                print(f"Error verifying record: {str(e)}")
        
        return True
    except Exception as e:
        print(f"Error in direct_save_form_data: {str(e)}")
        
        if conn:
            try:
                conn.close()
            except:
                pass
        
        return False

def direct_phone_exists(phone_number):
    """Check if a phone number exists directly using psycopg2"""
    conn = get_direct_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if column exists before querying
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'feedback_db' AND column_name = 'phone'
            );
        """)
        
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            # Add the column if it doesn't exist
            check_phone_column_exists()
            return False  # Since the column was just added, the phone number can't exist yet
        
        # Query for the phone number
        cursor.execute("""
            SELECT COUNT(*) FROM feedback_db WHERE phone = %s;
        """, (phone_number,))
        
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return count > 0
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', True):
            print(f"Error checking phone number in database: {str(e)}")
        return False

def get_phone_count(phone_number):
    """Check how many times a phone number appears in the database and return the count"""
    conn = get_direct_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        
        # Check if column exists before querying
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'feedback_db' AND column_name = 'phone'
            );
        """)
        
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            # Add the column if it doesn't exist
            check_phone_column_exists()
            return 0  # Since the column was just added, the phone number can't exist yet
        
        # Query for the phone number count
        cursor.execute("""
            SELECT COUNT(*) FROM feedback_db WHERE phone = %s;
        """, (phone_number,))
        
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return count
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', True):
            print(f"Error checking phone number count in database: {str(e)}")
        return 0

def phone_exists_in_database(phone_number):
    """Check if the phone number already exists in the database"""
    try:
        session = get_db_session()
        if not session:
            return direct_phone_exists(phone_number)
        
        # Query for existing phone number
        existing_record = session.query(Feedback).filter(Feedback.phone == phone_number).first()
        
        # Close the session
        session.close()
        
        # Return True if the phone number already exists
        return existing_record is not None
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            print(f"Error checking phone number in database: {str(e)}")
        return direct_phone_exists(phone_number)

def save_form_data(form_data):
    """Save form data to the database"""
    try:
        print("Starting save_form_data with SQLAlchemy...")
        
        session = get_db_session()
        if not session:
            print("No database session available")
            # Fall back to direct database operations without UI messages
            print("Falling back to direct database operations")
            return direct_save_form_data(form_data)
        
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
        
        # Safely extract values from form_data with default empty strings
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
        session.close()
        return True
    except Exception as e:
        print(f"Error in save_form_data: {str(e)}")
        # Print more detail about the error - console only
        error_trace = traceback.format_exc()
        print("Error details:", error_trace)
        
        # Fall back to direct database operations
        try:
            print("Falling back to direct database operations after error")
            return direct_save_form_data(form_data)
        except Exception as e2:
            print(f"Error in fallback save: {str(e2)}")
            return False

def get_phone_occurrence_count(phone_number):
    """Check how many times a phone number appears in the database"""
    try:
        session = get_db_session()
        if not session:
            # Fall back to direct database operations if session can't be created
            return get_phone_count(phone_number)
        
        # Query for phone number occurrences
        count = session.query(Feedback).filter(Feedback.phone == phone_number).count()
        
        # Close the session
        session.close()
        
        # Return the count
        return count
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            print(f"Error checking phone number count in database: {str(e)}")
        
        # Fall back to direct database operations
        try:
            return get_phone_count(phone_number)
        except Exception:
            return 0 

if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
    # Set branch from URL
    query_params = st.query_params
    branch = query_params.get('branch', [None])[0]
    if branch:
        st.session_state.form_data['branch'] = branch

st.session_state.form_data = {}
query_params = st.query_params
branch = query_params.get('branch', [None])[0]
if branch:
    st.session_state.form_data['branch'] = branch
        
