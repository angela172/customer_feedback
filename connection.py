import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from database import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT
# Create a cached database connection function
@st.cache_resource
def init_connection():
    """Initialize database connection. This function will be cached and only run once, unless invalidated"""
    try:
        # Database credentials for remote PostgreSQL server
        '''DB_HOST = "103.173.18.175"
        DB_PORT = 5432
        DB_NAME = "CustomerFeedback"
        DB_USERNAME = "postgres"  # You may need to update this
        DB_PASSWORD = "Po$tgr3$18Sol"  # You may need to update this'''
        
        # PostgreSQL connection string
        DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
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
