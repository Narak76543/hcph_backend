from sqlalchemy import Column, Integer, String
from core.db import Base

class Customer(Base):
    __tablename__ = "tbl_customer"
    id           = Column(Integer, primary_key=True, index=True)
    first_name   = Column(String, index=True)
    last_name    = Column(String, index=True)
    email        = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)
