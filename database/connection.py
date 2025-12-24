from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models.order import Base


class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def connect(self, database_path: str = "./test.db"):
        if "://" in database_path:
            self._engine = create_engine(database_path, echo=False)
        else:
            self._engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        
        Base.metadata.create_all(self._engine)

    def get_session(self) -> Session:
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._session_factory()

    def close(self):
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def engine(self):
        return self._engine

    @property
    def is_connected(self) -> bool:
        return self._engine is not None


_db_connection: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection
