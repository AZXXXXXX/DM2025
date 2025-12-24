import uuid
from datetime import datetime
from enum import IntEnum
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from models.order import Base
from enums import ReturnReason

if TYPE_CHECKING:
    from models.inventory import Inventory


class ReturnStatus(IntEnum):
    PENDING = 0
    APPROVED = 1
    REJECTED = 2
    COMPLETE = 3

    def __str__(self) -> str:
        mapping = {
            ReturnStatus.PENDING: "待审核",
            ReturnStatus.APPROVED: "已批准",
            ReturnStatus.REJECTED: "已拒绝",
            ReturnStatus.COMPLETE: "已完成",
        }
        return mapping.get(self, "未知")


class ReturnRequest(Base):
    __tablename__ = 'return_request'
    __allow_unmapped__ = True
    
    return_request_id = Column('return_request_id', String(64), primary_key=True)
    order_id = Column('order_id', String(50), nullable=False, index=True)
    product_id = Column('product_id', String(64), ForeignKey('inventory.product_id'), nullable=False)
    quantity = Column('quantity', Integer, nullable=False)
    reason = Column('reason', Integer, nullable=False)
    description = Column('description', Text, default='')
    status = Column('status', Integer, default=ReturnStatus.PENDING)
    customer_name = Column('customer_name', String(200), nullable=False)
    reviewer_id = Column('reviewer_id', String(64), nullable=True)
    review_comment = Column('review_comment', Text, default='')
    reviewed_at = Column('reviewed_at', DateTime, nullable=True)
    created_at = Column('created_at', DateTime, default=datetime.now)
    updated_at = Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)

    product: 'Inventory' = relationship('Inventory', back_populates='return_requests')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.return_request_id:
            self.generate_return_request_id()

    def generate_return_request_id(self):
        self.return_request_id = f"RET-{str(uuid.uuid4())[:8]}"

    def validate(self) -> bool:
        return bool(
            self.order_id and
            self.product_id and
            self.quantity > 0 and
            self.customer_name
        )

    @property
    def status_enum(self) -> ReturnStatus:
        return ReturnStatus(self.status)

    @property
    def reason_enum(self) -> ReturnReason:
        return ReturnReason(self.reason)
