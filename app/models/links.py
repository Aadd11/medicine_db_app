from sqlalchemy import Table, Column, ForeignKey
from .base import Base

medicine_type_link = Table(
    'medicine_type_link', Base.metadata,
    Column('medicine_id', ForeignKey('medicines.id'), primary_key=True),
    Column('type_id', ForeignKey('medicine_types.id'), primary_key=True)
)
