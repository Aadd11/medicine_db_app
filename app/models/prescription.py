from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import Base
class Prescription(Base):
    __tablename__ = 'prescriptions'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    medicine_id = Column(Integer, ForeignKey('medicines.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)

    customer = relationship("Customer", back_populates="prescriptions")
    medicine = relationship("Medicine", back_populates="prescriptions")
    employee = relationship("Employee", back_populates="prescriptions")
