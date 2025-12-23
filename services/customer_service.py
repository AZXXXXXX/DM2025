

from typing import List, Optional

from models import Customer
from enums import CustomerType
from database import CustomerRepository
from database.customer_repository import CustomerNotFoundError


class CustomerService:
    

    def __init__(self):
        
        self._customer_repo = CustomerRepository()

    def create_customer(self, customer: Customer) -> None:
        
        if not customer.validate():
            raise ValueError("Invalid customer data")
        self._customer_repo.create_customer(customer)

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        
        try:
            return self._customer_repo.get_customer_by_id(customer_id)
        except CustomerNotFoundError:
            return None

    def get_customer_by_company_name(self, company_name: str) -> Optional[Customer]:
        
        try:
            return self._customer_repo.get_customer_by_company_name(company_name)
        except CustomerNotFoundError:
            return None

    def update_customer(self, customer: Customer) -> None:
        
        self._customer_repo.update_customer(customer)

    def delete_customer(self, customer_id: str) -> None:
        
        self._customer_repo.delete_customer(customer_id)

    def get_all_customers(self) -> List[Customer]:
        
        return self._customer_repo.find_all_customers()

    def get_customers_by_customer_type(
        self, customer_type: CustomerType
    ) -> List[Customer]:
        
        return self._customer_repo.find_customers_by_customer_type(customer_type)

    def get_active_customers(self) -> List[Customer]:
        
        return self._customer_repo.find_active_customers()

    def search_customers(self, keyword: str) -> List[Customer]:
        
        return self._customer_repo.search_customers(keyword)

    def get_customer_count(self) -> int:
        
        return self._customer_repo.count()

    def get_or_create_customer(
        self, company_name: str, customer_type: CustomerType
    ) -> Optional[Customer]:
        
        try:
            return self._customer_repo.get_or_create_customer(company_name, customer_type)
        except Exception:
            return None
