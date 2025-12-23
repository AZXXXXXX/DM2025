

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models import Customer
from enums import CustomerType
from database.connection import get_db


class CustomerRepositoryError(Exception):
    
    pass


class CustomerNotFoundError(CustomerRepositoryError):
    
    pass


class CustomerAlreadyExistsError(CustomerRepositoryError):
    
    pass


class CustomerRepository:
    

    def __init__(self):
        
        self._db = get_db()

    def _get_session(self) -> Session:
        
        return self._db.get_session()

    def create_customer(self, customer: Customer) -> None:
        
        if not customer.validate():
            raise ValueError("Invalid customer data")
        
        if not customer.customer_id:
            customer.customer_id = str(uuid.uuid4())
        
        session = self._get_session()
        try:
                                          
            existing = session.query(Customer).filter(
                Customer.company_name == customer.company_name
            ).first()
            if existing:
                raise CustomerAlreadyExistsError(
                    f"Customer '{customer.company_name}' already exists"
                )
            customer.customer_type = int(customer.customer_type)

            session.add(customer)
            session.commit()
        except CustomerAlreadyExistsError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_customer_by_id(self, customer_id: str) -> Customer:
        
        session = self._get_session()
        try:
            customer = session.query(Customer).filter(
                Customer.customer_id == customer_id
            ).first()
            if not customer:
                raise CustomerNotFoundError(
                    f"Customer with ID '{customer_id}' not found"
                )
            return customer
        finally:
            session.close()

    def get_customer_by_company_name(self, company_name: str) -> Customer:
        
        session = self._get_session()
        try:
            customer = session.query(Customer).filter(
                Customer.company_name == company_name
            ).first()
            if not customer:
                raise CustomerNotFoundError(
                    f"Customer '{company_name}' not found"
                )
            return customer
        finally:
            session.close()

    def update_customer(self, customer: Customer) -> None:
        
        if not customer.customer_id:
            raise ValueError("Customer ID is required")
        
        session = self._get_session()
        try:
            existing = session.query(Customer).filter(
                Customer.customer_id == customer.customer_id
            ).first()
            if not existing:
                raise CustomerNotFoundError(
                    f"Customer with ID '{customer.customer_id}' not found"
                )
            customer.customer_type = int(customer.customer_type)

            for key, value in customer.__dict__.items():
                if not key.startswith('_') and key != 'customer_id':
                    setattr(existing, key, value)
            
            session.commit()
        except CustomerNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_customer(self, customer_id: str) -> None:
        
        session = self._get_session()
        try:
            result = session.query(Customer).filter(
                Customer.customer_id == customer_id
            ).delete()
            if result == 0:
                raise CustomerNotFoundError(
                    f"Customer with ID '{customer_id}' not found"
                )
            session.commit()
        except CustomerNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_all_customers(self) -> List[Customer]:
        
        session = self._get_session()
        try:
            return session.query(Customer).all()
        finally:
            session.close()

    def find_customers_by_customer_type(
        self, customer_type: CustomerType
    ) -> List[Customer]:
        
        session = self._get_session()
        try:
            return session.query(Customer).filter(
                Customer.customer_type == int(customer_type)
            ).all()
        finally:
            session.close()

    def find_active_customers(self) -> List[Customer]:
        
        session = self._get_session()
        try:
            return session.query(Customer).filter(Customer.is_active == True).all()
        finally:
            session.close()

    def find_customers_by_city(self, city: str) -> List[Customer]:
        
        session = self._get_session()
        try:
            return session.query(Customer).filter(
                Customer.city.like(f"%{city}%")
            ).all()
        finally:
            session.close()

    def search_customers(self, keyword: str) -> List[Customer]:
        
        session = self._get_session()
        try:
            return session.query(Customer).filter(
                (Customer.company_name.like(f"%{keyword}%")) |
                (Customer.contact_person.like(f"%{keyword}%")) |
                (Customer.address.like(f"%{keyword}%"))
            ).all()
        finally:
            session.close()

    def count(self) -> int:
        
        session = self._get_session()
        try:
            return session.query(Customer).count()
        finally:
            session.close()

    def get_or_create_customer(
        self, company_name: str, customer_type: CustomerType
    ) -> Customer:
        
        session = self._get_session()
        try:
            customer = session.query(Customer).filter(
                Customer.company_name == company_name
            ).first()
            
            if customer:
                return customer
            
                                 
            customer = Customer(
                customer_id=str(uuid.uuid4()),
                company_name=company_name,
                customer_type=int(customer_type),
                is_active=True,
            )
            session.add(customer)
            session.commit()
            return customer
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
