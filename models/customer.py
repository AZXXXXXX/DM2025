import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship, Mapped

from models.order import Base
from enums import CustomerType

if TYPE_CHECKING:
    from models.order import Order


class Customer(Base):
    __tablename__ = 'customer'
    __allow_unmapped__ = True
    
    customer_id = Column('customer_id', String(64), primary_key=True)
    company_name = Column('company_name', String(200), unique=True, nullable=False, index=True)
    customer_type = Column('customer_type', Integer, default=CustomerType.UNKNOWN)
    contact_person = Column('contact_person', String(50), default='')
    contact_phone = Column('contact_phone', String(20), default='')
    contact_email = Column('contact_email', String(100), default='')
    address = Column('address', String(500), default='')
    city = Column('city', String(50), default='')
    province = Column('province', String(50), default='')
    postal_code = Column('postal_code', String(10), default='')
    tax_id = Column('tax_id', String(50), default='')
    credit_level = Column('credit_level', Integer, default=3)
    notes = Column('notes', Text, default='')
    is_active = Column('is_active', Boolean, default=True)
    created_at = Column('created_at', DateTime, default=datetime.now)
    updated_at = Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)

    orders: List['Order'] = relationship('Order', back_populates='customer')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.customer_id:
            self.customer_id = str(uuid.uuid4())

    def validate(self) -> bool:
        return self.company_name and len(self.company_name) >= 2

    def get_credit_level_string(self) -> str:
        mapping = {
            5: "优秀",
            4: "良好",
            3: "一般",
            2: "较差",
            1: "差",
        }
        return mapping.get(self.credit_level, "未知")

    @property
    def customer_type_enum(self) -> CustomerType:
        return CustomerType(self.customer_type)
