import hashlib
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

from enums import OrderStatus, CustomerType

if TYPE_CHECKING:
    from models.customer import Customer
    from models.inventory import Inventory
    from models.user import User

Base = declarative_base()


class Order(Base):
    __tablename__ = 'order'
    __allow_unmapped__ = True
    
    hash = Column('Hash', String(64), primary_key=True, nullable=False)
    customer_type = Column('customer_type', Integer, default=CustomerType.UNKNOWN)
    customer_name = Column('customer_name', String(200), nullable=False)
    sales = Column('sales', String(100), nullable=False)
    order_id = Column('order_id', String(50), nullable=False, index=True)
    tracking_number = Column('tracking_number', String(100), default='')
    status = Column('status', Integer, nullable=False, default=OrderStatus.NEW)
    order_time = Column('order_time', DateTime, nullable=False)
    payment_time = Column('payment_time', DateTime, nullable=True)
    ship_deadline = Column('ship_deadline', DateTime, nullable=True)
    product_id = Column('product_id', String(64), ForeignKey('inventory.product_id'), nullable=False)
    quantity = Column('quantity', Integer, nullable=False, default=1)
    return_request_id = Column('return_request_id', String(64), index=True, nullable=True)
    customer_id = Column('customer_id', String(64), ForeignKey('customer.customer_id'), index=True, nullable=True)
    created_by_id = Column('created_by_id', String(64), ForeignKey('user.user_id'), index=True, nullable=True)
    return_applied = Column('return_applied', Boolean, default=False)
    created_at = Column('created_at', DateTime, default=datetime.now)
    updated_at = Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)

    customer = relationship('Customer', back_populates='orders', foreign_keys=[customer_id])
    product = relationship('Inventory', back_populates='orders', foreign_keys=[product_id])
    created_by = relationship('User', back_populates='created_orders', foreign_keys=[created_by_id])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.hash:
            self.generate_hash()

    def check_entity(self) -> bool:
        return bool(self.order_id and self.product_id and self.customer_name)

    def generate_hash(self):
        customer_type_str = str(CustomerType(self.customer_type)) if self.customer_type else ""
        ship_deadline_str = self.ship_deadline.strftime("%Y-%m-%d") if self.ship_deadline else ""
        
        hash_data = (
            (self.order_id or '') +
            (self.product_id or '') +
            customer_type_str +
            (self.sales or '') +
            (self.customer_name or '') +
            ship_deadline_str
        )
        
        h = hashlib.sha256()
        h.update(hash_data.encode('utf-8'))
        self.hash = h.hexdigest()

    def to_array(self) -> list:
        payment_time_str = ""
        if self.payment_time:
            payment_time_str = self.payment_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return [
            str(CustomerType(self.customer_type)),
            self.customer_name or '',
            self.sales or '',
            self.order_id or '',
            self.tracking_number or '',
            str(OrderStatus(self.status)),
            self.order_time.strftime("%Y-%m-%d %H:%M:%S") if self.order_time else '',
            payment_time_str,
            self.ship_deadline.strftime("%Y-%m-%d %H:%M:%S") if self.ship_deadline else '',
            self.product_id or '',
            str(self.quantity),
            self.return_request_id or '',
        ]

    @property
    def status_enum(self) -> OrderStatus:
        return OrderStatus(self.status)

    @property
    def customer_type_enum(self) -> CustomerType:
        return CustomerType(self.customer_type)
