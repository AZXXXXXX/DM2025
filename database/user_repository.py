import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from models import User
from enums import UserRole
from database.connection import get_db


class UserRepositoryError(Exception):
    pass


class UserNotFoundError(UserRepositoryError):
    pass


class UserAlreadyExistsError(UserRepositoryError):
    pass


class InvalidCredentialsError(UserRepositoryError):
    pass


class UserRepository:
    def __init__(self):
        self._db = get_db()

    def _get_session(self) -> Session:
        return self._db.get_session()

    def ensure_default_admin(self) -> None:
        session = self._get_session()
        try:
            count = session.query(User).count()
            if count == 0:
                admin = User(
                    user_id=str(uuid.uuid4()),
                    username="admin",
                    display_name="系统管理员",
                    role=int(UserRole.ADMIN),
                    department="系统",
                    is_active=True,
                )
                admin.set_password("admin123")
                session.add(admin)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def create_user(self, user: User) -> None:
        if not user.validate():
            raise ValueError("Invalid user data")
        
        if not user.user_id:
            user.user_id = str(uuid.uuid4())
        
        session = self._get_session()
        try:
            existing = session.query(User).filter(User.username == user.username).first()
            if existing:
                raise UserAlreadyExistsError(f"User '{user.username}' already exists")
            user.role = int(user.role)
            session.add(user)
            session.commit()
        except UserAlreadyExistsError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_by_id(self, user_id: str) -> User:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserNotFoundError(f"User with ID '{user_id}' not found")
            return user
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> User:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                raise UserNotFoundError(f"User '{username}' not found")
            return user
        finally:
            session.close()

    def authenticate(self, username: str, password: str) -> User:
        session = self._get_session()
        try:
            user = session.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if not user:
                raise InvalidCredentialsError("Invalid username or password")
            
            if not user.check_password(password):
                raise InvalidCredentialsError("Invalid username or password")
            
            user.last_login_at = datetime.now()
            session.commit()
            
            session.expunge(user)
            
            return user
        except InvalidCredentialsError:
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_user(self, user: User) -> None:
        if not user.user_id:
            raise ValueError("User ID is required")
        
        session = self._get_session()
        try:
            existing = session.query(User).filter(User.user_id == user.user_id).first()
            if not existing:
                raise UserNotFoundError(f"User with ID '{user.user_id}' not found")
            user.role = int(user.role)
            for key, value in user.__dict__.items():
                if not key.startswith('_') and key != 'user_id':
                    setattr(existing, key, value)
            
            session.commit()
        except UserNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_password(self, user_id: str, new_password: str) -> None:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserNotFoundError(f"User with ID '{user_id}' not found")
            
            user.set_password(new_password)
            session.commit()
        except UserNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_user(self, user_id: str) -> None:
        session = self._get_session()
        try:
            result = session.query(User).filter(User.user_id == user_id).delete()
            if result == 0:
                raise UserNotFoundError(f"User with ID '{user_id}' not found")
            session.commit()
        except UserNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_all_users(self) -> List[User]:
        session = self._get_session()
        try:
            return session.query(User).all()
        finally:
            session.close()

    def find_users_by_role(self, role: UserRole) -> List[User]:
        session = self._get_session()
        try:
            return session.query(User).filter(User.role == int(role)).all()
        finally:
            session.close()

    def find_active_users(self) -> List[User]:
        session = self._get_session()
        try:
            return session.query(User).filter(User.is_active == True).all()
        finally:
            session.close()

    def count(self) -> int:
        session = self._get_session()
        try:
            return session.query(User).count()
        finally:
            session.close()
