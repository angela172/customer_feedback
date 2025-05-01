from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Get the absolute path to the database directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'feedback.db')

# Ensure the database directory exists
os.makedirs(current_dir, exist_ok=True)

# Create SQLite database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

print(f"Database path: {db_path}")  # Debug print

# Create SQLAlchemy engine with echo=True for debugging
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

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
        return False

def get_db_session():
    """Get database session"""
    try:
        print("Creating new database session...")  # Debug print
        db = SessionLocal()
        try:
            yield db
        finally:
            print("Closing database session...")  # Debug print
            db.close()
    except Exception as e:
        print(f"Error creating database session: {str(e)}")
        raise 