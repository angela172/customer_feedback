from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Feedback(Base):
    __tablename__ = 'feedback_db'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    language = Column(String(50))
    nps = Column(Integer)
    first_visit = Column(String(50))
    satisfaction = Column(String(50))
    satisfaction_reason = Column(String(255))
    dissatisfaction_reason = Column(String(255))
    dissatisfaction_reason_text = Column(Text)
    feedback = Column(Text)
    branch = Column(String(255)) 
