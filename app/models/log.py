from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class ActionLog(Base):
    __tablename__ = 'action_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action_type = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)

    user = relationship("User", back_populates="logs")