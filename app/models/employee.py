from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from .base import Base

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    position = Column(String)
    salary = Column(Float)

    user = relationship("User", back_populates="employee", uselist=False)
    prescriptions = relationship("Prescription", back_populates="employee")
    sales = relationship("Sale", back_populates="employee")
