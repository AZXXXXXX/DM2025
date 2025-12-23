

from datetime import datetime
from typing import List, Optional

from models import Order
from enums import OrderStatus, CustomerType, UserRole
from database import OrderRepository


class OrderService:
    

    def __init__(self, user_service=None):
        
        self._order_repo = OrderRepository()
        self._user_service = user_service

    def set_user_service(self, user_service):
        
        self._user_service = user_service

    def _filter_by_customer(self, orders: List[Order]) -> List[Order]:
        
        if not self._user_service:
            return orders
        
        current_user = self._user_service.get_current_user()
        if not current_user:
            return orders
        
                                                
        if current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return orders
        
                                                                                     
        if current_user.role == UserRole.CUSTOMER:
            customer_name = current_user.display_name
            return [order for order in orders if order.customer_name == customer_name]
        
        return orders

    def create_order(self, order: Order) -> None:
        
        if not order.check_entity():
            raise ValueError("Invalid order data")
        self._order_repo.create_order(order)

    def get_orders_by_filter(
        self,
        order_id: str = "",
        customer_name: str = "",
        sales: str = "",
        status: Optional[OrderStatus] = None,
        customer_type: Optional[CustomerType] = None,
        ship_deadline: Optional[datetime] = None
    ) -> List[Order]:
        
        orders = self._order_repo.find(
            order_id, customer_name, sales, status, customer_type, ship_deadline
        )
        return self._filter_by_customer(orders)

    def get_all_orders(self) -> List[Order]:
        
        orders = self._order_repo.find_all()
        return self._filter_by_customer(orders)

    def get_orders_by_order_id(self, order_id: str) -> List[Order]:
        
        orders = self._order_repo.find_by_order_id(order_id)
        return self._filter_by_customer(orders)

    def get_orders_by_product_id(self, product_id: str) -> List[Order]:
        
        orders = self._order_repo.find_by_product_id(product_id)
        return self._filter_by_customer(orders)

    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        
        orders = self._order_repo.find_by_status(status)
        return self._filter_by_customer(orders)

    def get_orders_by_customer_type(self, customer_type: CustomerType) -> List[Order]:
        
        orders = self._order_repo.find_by_customer_type(customer_type)
        return self._filter_by_customer(orders)

    def get_orders_by_ship_deadline(self, deadline: datetime) -> List[Order]:
        
        orders = self._order_repo.find_by_ship_deadline(deadline)
        return self._filter_by_customer(orders)

    def get_orders_by_sales(self, sales: str) -> List[Order]:
        
        orders = self._order_repo.find_by_sales(sales)
        return self._filter_by_customer(orders)

    def get_orders_by_customer_name(self, customer_name: str) -> List[Order]:
        
        orders = self._order_repo.find_by_customer_name(customer_name)
        return self._filter_by_customer(orders)

    def update_order(self, order: Order) -> None:
        
        if not order.check_entity():
            raise ValueError("Invalid order data")
        self._order_repo.update_order(order)

    def delete_order(self, order: Order) -> None:
        
        self._order_repo.delete_order(order)

    def get_order_count(self) -> int:
        
        return self._order_repo.count()

    def import_orders(self, orders: List[Order]) -> tuple:
        
        added_orders = []
        success = 0
        
        for order in orders:
            try:
                self.create_order(order)
                added_orders.append(order)
                success += 1
            except Exception as e:
                                                  
                for added_order in added_orders:
                    try:
                        self.delete_order(added_order)
                    except Exception:
                        pass
                return 0, len(orders), e
        
        return success, 0, None

    def get_orders_nearing_deadline(self, days: int) -> List[Order]:
        
        customer_id = self._get_customer_id_filter()
        return self._order_repo.find_nearing_deadline(days, customer_id)

    def _get_customer_id_filter(self) -> str:
        
        if not self._user_service:
            return ""
        
        current_user = self._user_service.get_current_user()
        if not current_user:
            return ""
        
                                                
        if current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return ""
        
        return ""
