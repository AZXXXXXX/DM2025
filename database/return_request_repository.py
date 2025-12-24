from typing import List, Optional

from sqlalchemy.orm import Session

from models import ReturnRequest, ReturnStatus
from database.connection import get_db


class ReturnRequestRepositoryError(Exception):
    pass


class ReturnRequestNotFoundError(ReturnRequestRepositoryError):
    pass


class ReturnRequestAlreadyExistsError(ReturnRequestRepositoryError):
    pass


class ReturnRequestRepository:
    def __init__(self):
        self._db = get_db()

    def _get_session(self) -> Session:
        return self._db.get_session()

    def create_return_request(self, return_request: ReturnRequest) -> None:
        if not return_request.validate():
            raise ValueError("Invalid return request data")
        
        if not return_request.return_request_id:
            return_request.generate_return_request_id()
        
        session = self._get_session()
        try:
            existing = session.query(ReturnRequest).filter(
                ReturnRequest.return_request_id == return_request.return_request_id
            ).first()
            if existing:
                raise ReturnRequestAlreadyExistsError(
                    f"Return request with ID '{return_request.return_request_id}' already exists"
                )
            
            session.add(return_request)
            session.commit()
        except ReturnRequestAlreadyExistsError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_return_request_by_id(self, return_request_id: str) -> ReturnRequest:
        session = self._get_session()
        try:
            return_request = session.query(ReturnRequest).filter(
                ReturnRequest.return_request_id == return_request_id
            ).first()
            if not return_request:
                raise ReturnRequestNotFoundError(
                    f"Return request with ID '{return_request_id}' not found"
                )
            return return_request
        finally:
            session.close()

    def find_by_order_id(self, order_id: str) -> List[ReturnRequest]:
        session = self._get_session()
        try:
            return session.query(ReturnRequest).filter(
                ReturnRequest.order_id == order_id
            ).all()
        finally:
            session.close()

    def find_all(self) -> List[ReturnRequest]:
        session = self._get_session()
        try:
            return session.query(ReturnRequest).all()
        finally:
            session.close()

    def find_by_status(self, status: ReturnStatus) -> List[ReturnRequest]:
        session = self._get_session()
        try:
            return session.query(ReturnRequest).filter(
                ReturnRequest.status == int(status)
            ).all()
        finally:
            session.close()

    def update_return_request(self, return_request: ReturnRequest) -> None:
        if not return_request.return_request_id:
            raise ValueError("Return request ID is required")
        
        session = self._get_session()
        try:
            existing = session.query(ReturnRequest).filter(
                ReturnRequest.return_request_id == return_request.return_request_id
            ).first()
            if not existing:
                raise ReturnRequestNotFoundError(
                    f"Return request with ID '{return_request.return_request_id}' not found"
                )
            
            updateable_fields = [
                'order_id', 'product_id', 'quantity', 'reason', 'description',
                'status', 'customer_name', 'reviewer_id', 'review_comment', 'reviewed_at'
            ]
            return_request.status = int(return_request.status)
            return_request.reason = int(return_request.reason)
            for field_name in updateable_fields:
                if hasattr(return_request, field_name):
                    setattr(existing, field_name, getattr(return_request, field_name))
            
            session.commit()
        except ReturnRequestNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_return_request(self, return_request_id: str) -> None:
        session = self._get_session()
        try:
            result = session.query(ReturnRequest).filter(
                ReturnRequest.return_request_id == return_request_id
            ).delete()
            if result == 0:
                raise ReturnRequestNotFoundError(
                    f"Return request with ID '{return_request_id}' not found"
                )
            session.commit()
        except ReturnRequestNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def count(self) -> int:
        session = self._get_session()
        try:
            return session.query(ReturnRequest).count()
        finally:
            session.close()
