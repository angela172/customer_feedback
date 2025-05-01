import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env file if it exists
load_dotenv()

def get_database_credentials():
    """Get database credentials from .env file if running locally, otherwise from Streamlit secrets"""
    try:
        if os.path.exists(r'C:\Users\layas\Desktop\Sol_Analytics\Customer Feedback Form\.env'):
        # Try to get credentials from .env file first (local development)
            return {
                'username': os.getenv('DB_USERNAME'),
                'password': os.getenv('DB_PASSWORD'),
                'host': os.getenv('DB_HOST'),
                'port': os.getenv('DB_PORT'),
                'database': os.getenv('DB_NAME')
            }
        
        # If .env doesn't exist, try to get from Streamlit secrets (cloud deployment)
        return {
            'username': st.secrets["username"],
            'password': st.secrets["password"],
            'host': st.secrets["host"],
            'port': st.secrets["port"],
            'database': st.secrets["database"]
        }
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            st.error(f"Error getting database credentials: {str(e)}")
        return None

# Create a cached database connection function
@st.cache_resource
def init_connection():
    """Initialize database connection. This function will be cached and only run once, unless invalidated"""
    try:
        # Get database credentials
        credentials = get_database_credentials()
        if not credentials:
            raise Exception("Could not get database credentials")
        
        # PostgreSQL connection string
        DATABASE_URL = f"postgresql+psycopg2://{credentials['username']}:{credentials['password']}@{credentials['host']}:{credentials['port']}/{credentials['database']}"
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        return engine
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            st.error(f"Database connection error: {str(e)}")
        return None

def get_db_session():
    """Get a database session"""
    engine = init_connection()
    if engine:
        Session = sessionmaker(bind=engine)
        return Session()
    return None

def init_database_tables():
    """Create tables if they don't exist"""
    engine = init_connection()
    
    if not engine:
        if st.session_state.get('DEBUG_MODE', False):
            st.error("Cannot initialize tables: No database connection")
        return False
    
    try:
        Base.metadata.create_all(engine)
        if st.session_state.get('DEBUG_MODE', False):
            print("Database tables initialized successfully")
        return True
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            st.error(f"Error creating database tables: {str(e)}")
        return False 
