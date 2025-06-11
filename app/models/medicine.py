from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .links import medicine_type_link
from .base import Base

class Medicine(Base):
    __tablename__ = 'medicines'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    prescription_required = Column(Boolean, default=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))

    supplier = relationship("Supplier", back_populates="medicines")
    types = relationship("MedicineType", secondary=medicine_type_link, back_populates="medicines")
    prescriptions = relationship("Prescription", back_populates="medicine")
    sales = relationship("Sale", back_populates="medicine")