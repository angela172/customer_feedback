from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Get the absolute path to the database directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'feedback.db')

# Ensure the database directory exists and is writable
os.makedirs(current_dir, exist_ok=True)

# Create SQLite database URL with absolute path
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

print(f"Database path: {db_path}")  # Debug print
print(f"Database directory exists: {os.path.exists(current_dir)}")  # Debug print
print(f"Database directory writable: {os.access(current_dir, os.W_OK)}")  # Debug print

# Create SQLAlchemy engine with echo=True for debugging and check_same_thread=False for Streamlit
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

def init_database_tables():
    """Initialize database tables"""
    try:
        print("Initializing database tables...")  # Debug print
        # Import models here to avoid circular imports
        from .models import Feedback
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully")  # Debug print
        return True
    except Exception as e:
        print(f"Error initializing database tables: {str(e)}")
        print(f"Database path: {db_path}")
        print(f"Current directory: {current_dir}")
        print(f"Directory permissions: {oct(os.stat(current_dir).st_mode)[-3:]}")
        return False

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Error creating database session: {str(e)}")
        raise 