

import threading
from typing import Optional, List

from models import User
from enums import UserRole
from database import UserRepository
from database.user_repository import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
)


class UserServiceError(Exception):
    
    pass


class NotLoggedInError(UserServiceError):
    
    pass


class PermissionDeniedError(UserServiceError):
    
    pass


class UserService:
    

    def __init__(self):
        
        self._user_repo = UserRepository()
        self._current_user: Optional[User] = None
        self._lock = threading.RLock()
        
                                     
        self._user_repo.ensure_default_admin()

    def login(self, username: str, password: str) -> User:
        
        user = self._user_repo.authenticate(username, password)
        
        with self._lock:
            self._current_user = user
        
        return user

    def logout(self) -> None:
        
        with self._lock:
            self._current_user = None

    def get_current_user(self) -> Optional[User]:
        
        with self._lock:
            return self._current_user

    def is_logged_in(self) -> bool:
        
        with self._lock:
            return self._current_user is not None

    def get_current_user_role(self) -> UserRole:
        
        with self._lock:
            if self._current_user:
                return UserRole(self._current_user.role)
            return UserRole.VIEWER

    def can_create(self) -> bool:
        
        with self._lock:
            if not self._current_user:
                return False
            return self._current_user.can_create()

    def can_update(self) -> bool:
        
        with self._lock:
            if not self._current_user:
                return False
            return self._current_user.can_update()

    def can_delete(self) -> bool:
        
        with self._lock:
            if not self._current_user:
                return False
            return self._current_user.can_delete()

    def can_manage_users(self) -> bool:
        
        with self._lock:
            if not self._current_user:
                return False
            return self._current_user.can_manage_users()

    def can_view_settings(self) -> bool:
        
        with self._lock:
            if not self._current_user:
                return False
            return self._current_user.can_view_settings()

    def create_user(self, user: User) -> None:
        
        if not self.can_manage_users():
            raise PermissionDeniedError("Permission denied")
        self._user_repo.create_user(user)

    def update_user(self, user: User) -> None:
        
        current_user = self.get_current_user()
        if not current_user:
            raise NotLoggedInError("Not logged in")
        
                                          
        if current_user.user_id != user.user_id and not current_user.can_manage_users():
            raise PermissionDeniedError("Permission denied")
        
        self._user_repo.update_user(user)

    def update_password(self, user_id: str, new_password: str) -> None:
        
        current_user = self.get_current_user()
        if not current_user:
            raise NotLoggedInError("Not logged in")
        
                                                  
        if current_user.user_id != user_id and not current_user.can_manage_users():
            raise PermissionDeniedError("Permission denied")
        
        self._user_repo.update_password(user_id, new_password)

    def delete_user(self, user_id: str) -> None:
        
        if not self.can_manage_users():
            raise PermissionDeniedError("Permission denied")
        
        current_user = self.get_current_user()
        if current_user and current_user.user_id == user_id:
            raise ValueError("Cannot delete current user")
        
        self._user_repo.delete_user(user_id)

    def register_customer(self, user: User) -> None:
        
                             
        user.role = UserRole.CUSTOMER
        user.is_active = True
        self._user_repo.create_user(user)

    def get_all_users(self) -> List[User]:
        
        if not self.can_manage_users():
            raise PermissionDeniedError("Permission denied")
        return self._user_repo.find_all_users()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        
        try:
            return self._user_repo.get_user_by_id(user_id)
        except UserNotFoundError:
            return None

    def get_user_count(self) -> int:
        
        return self._user_repo.count()
