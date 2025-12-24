import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship, Mapped

from models.order import Base
from enums import InventoryStatus

if TYPE_CHECKING:
    from models.order import Order
    from models.return_request import ReturnRequest


class Inventory(Base):
    __tablename__ = 'inventory'
    __allow_unmapped__ = True
    
    product_id = Column('product_id', String(64), primary_key=True)
    product_type = Column('product_type', String(100), nullable=False)
    manufacturer = Column('manufacturer', String(200), nullable=False)
    product_name = Column('product_name', String(200), nullable=False, index=True)
    product_model = Column('product_model', String(100), default='')
    stock_quantity = Column('stock_quantity', Integer, default=0)
    sold_quantity = Column('sold_quantity', Integer, default=0)
    status = Column('status', Integer, default=InventoryStatus.NORMAL)
    expected_arrival = Column('expected_arrival', DateTime, nullable=True)
    created_at = Column('created_at', DateTime, default=datetime.now)
    updated_at = Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)

    orders: List['Order'] = relationship('Order', back_populates='product')
    return_requests: List['ReturnRequest'] = relationship('ReturnRequest', back_populates='product')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.product_id:
            self.product_id = str(uuid.uuid4())

    def validate(self) -> bool:
        return bool(self.product_name and self.product_type and self.manufacturer)

    def update_status(self):
        if self.stock_quantity < 0:
            self.status = int(InventoryStatus.OUT_OF_STOCK)
        else:
            self.status = int(self.status)

    def to_array(self) -> list:
        expected_arrival_str = ""
        if self.expected_arrival:
            expected_arrival_str = self.expected_arrival.strftime("%Y-%m-%d")
        
        return [
            self.product_type or '',
            self.manufacturer or '',
            self.product_name or '',
            self.product_model or '',
            self.product_id or '',
            str(self.stock_quantity),
            str(self.sold_quantity),
            str(InventoryStatus(self.status)),
            expected_arrival_str,
        ]

    def to_public_array(self) -> list:
        return [
            self.product_name or '',
            self.product_id or '',
            str(self.stock_quantity),
        ]

    @property
    def status_enum(self) -> InventoryStatus:
        return InventoryStatus(self.status)
