from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'admin' or 'user'
    remember_me = Column(Boolean, default=False)

    employee = relationship("Employee", back_populates="user")
    logs = relationship("ActionLog", back_populates="user")