from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import Base

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    medicine_id = Column(Integer, ForeignKey('medicines.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # price at time of sale

    customer = relationship("Customer", back_populates="sales")
    medicine = relationship("Medicine", back_populates="sales")
    employee = relationship("Employee", back_populates="sales")
