from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Get the absolute path to the database directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'feedback.db')

# Create SQLite database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

def init_database_tables():
    """Initialize database tables"""
    try:
        # Import models here to avoid circular imports
        from .models import Feedback
        # Create all tables
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        print(f"Error initializing database tables: {str(e)}")
        return False

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 