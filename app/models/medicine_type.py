from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from .links import medicine_type_link
from .base import Base

class MedicineType(Base):
    __tablename__ = 'medicine_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    medicines = relationship("Medicine", secondary=medicine_type_link, back_populates="types")