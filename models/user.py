

import hashlib
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped

from models.order import Base
from enums import UserRole

if TYPE_CHECKING:
    from models.order import Order


class User(Base):
    
    
    __tablename__ = 'user'
    __allow_unmapped__ = True
    
    user_id = Column('user_id', String(64), primary_key=True)
    username = Column('username', String(50), unique=True, nullable=False, index=True)
    password_hash = Column('password_hash', String(128), nullable=False)
    display_name = Column('display_name', String(100), default='')
    role = Column('role', Integer, default=int(UserRole.VIEWER))
    department = Column('department', String(100), default='')
    email = Column('email', String(100), default='')
    phone = Column('phone', String(20), default='')
    is_active = Column('is_active', Boolean, default=True)
    created_at = Column('created_at', DateTime, default=datetime.now)
    updated_at = Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
    last_login_at = Column('last_login_at', DateTime, nullable=True)

                   
    created_orders: List['Order'] = relationship('Order', back_populates='created_by')

    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
        if not self.user_id:
            self.user_id = str(uuid.uuid4())

    def set_password(self, password: str):
        
        h = hashlib.sha256()
        h.update((password + self.username).encode('utf-8'))
        self.password_hash = h.hexdigest()

    def check_password(self, password: str) -> bool:
        
        h = hashlib.sha256()
        h.update((password + self.username).encode('utf-8'))
        calculated_hash = h.hexdigest()
        
        if len(calculated_hash) != len(self.password_hash):
            return False
        
        result = 0
        for a, b in zip(calculated_hash, self.password_hash):
            result |= ord(a) ^ ord(b)
        return result == 0

    def validate(self) -> bool:
        
        return (
            self.username and
            len(self.username) >= 3 and
            self.password_hash and
            len(self.password_hash) == 64
        )

    def can_create(self) -> bool:
        
        return self.is_active and self.role in [
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.OPERATOR
        ]

    def can_update(self) -> bool:
        
        return self.is_active and self.role in [
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.OPERATOR
        ]

    def can_delete(self) -> bool:
        
        return self.is_active and self.role in [
            UserRole.ADMIN,
            UserRole.MANAGER
        ]

    def can_manage_users(self) -> bool:
        
        return self.is_active and self.role == UserRole.ADMIN

    def can_view_settings(self) -> bool:
        
        return self.is_active and self.role in [
            UserRole.ADMIN,
            UserRole.MANAGER
        ]

    @property
    def role_enum(self) -> UserRole:
        
        return UserRole(self.role)
