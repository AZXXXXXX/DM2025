

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from models import Order, Inventory
from enums import OrderStatus, CustomerType, UserRole
from database import OrderRepository, CustomerRepository, InventoryRepository
from database.user_repository import UserRepository


@dataclass
class DashboardStats:
    
    total_orders: int = 0
    total_customers: int = 0
    total_users: int = 0
    total_products: int = 0
    pending_orders: int = 0
    completed_orders: int = 0
    near_deadline_orders: int = 0


@dataclass
class OrderStatusStats:
    
    status: OrderStatus
    count: int


@dataclass
class OrderCustomerTypeStats:
    
    customer_type: CustomerType
    count: int


@dataclass
class OrderSalesStats:
    
    sales: str
    count: int


@dataclass
class InventorySalesStats:
    
    product_type: str
    total_sold: int
    total_stock: int


@dataclass
class PlatformSalesStats:
    
    platform: str
    total_sold: int
    total_count: int


class StatisticsService:
    

    def __init__(self, user_service=None):
        
        self._order_repo = OrderRepository()
        self._customer_repo = CustomerRepository()
        self._user_repo = UserRepository()
        self._inventory_repo: Optional[InventoryRepository] = None
        self._user_service = user_service

    def set_user_service(self, user_service):
        
        self._user_service = user_service

    def set_inventory_repo(self, inventory_repo: InventoryRepository):
        
        self._inventory_repo = inventory_repo

    def _get_customer_id_filter(self) -> str:
        
        if not self._user_service:
            return ""
        
        current_user = self._user_service.get_current_user()
        if not current_user:
            return ""
        
                                              
        if current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return ""
        
        return ""

    def get_dashboard_stats(self) -> DashboardStats:
        
        stats = DashboardStats()
        
        stats.total_customers = self._customer_repo.count()
        stats.total_users = self._user_repo.count()
        
        if self._inventory_repo:
            stats.total_products = self._inventory_repo.count()
        
        customer_id = self._get_customer_id_filter()
        dashboard_counts = self._order_repo.get_dashboard_counts(customer_id)
        
        stats.total_orders = dashboard_counts.get("total_orders", 0)
        stats.pending_orders = dashboard_counts.get("pending_orders", 0)
        stats.completed_orders = dashboard_counts.get("completed_orders", 0)
        stats.near_deadline_orders = dashboard_counts.get("near_deadline_orders", 0)
        
        return stats

    def get_order_status_distribution(self) -> List[OrderStatusStats]:
        
        customer_id = self._get_customer_id_filter()
        status_counts = self._order_repo.count_by_status(customer_id)
        
        return [
            OrderStatusStats(
                status=item["status"],
                count=item["count"]
            )
            for item in status_counts
        ]

    def get_order_customer_type_distribution(self) -> List[OrderCustomerTypeStats]:
        
        customer_id = self._get_customer_id_filter()
        type_counts = self._order_repo.count_by_customer_type(customer_id)
        
        return [
            OrderCustomerTypeStats(
                customer_type=item["customer_type"],
                count=item["count"]
            )
            for item in type_counts
        ]

    def get_orders_by_sales(self) -> List[OrderSalesStats]:
        
        customer_id = self._get_customer_id_filter()
        sales_counts = self._order_repo.count_by_sales(customer_id)
        
        return [
            OrderSalesStats(
                sales=item["sales"],
                count=item["count"]
            )
            for item in sales_counts
        ]

    def get_deadline_distribution(self) -> Dict[str, int]:
        
        customer_id = self._get_customer_id_filter()
        return self._order_repo.get_deadline_stats(customer_id)

    def complex_query(self) -> List[Order]:
        
        customer_id = self._get_customer_id_filter()
        return self._order_repo.find_pending_orders_sorted(customer_id)

    def get_inventory_sales_stats(self) -> List[InventorySalesStats]:
        
        if not self._inventory_repo:
            return []
        
        stats = self._inventory_repo.get_sales_by_product_type()
        
        return [
            InventorySalesStats(
                product_type=item["product_type"],
                total_sold=item["total_sold"],
                total_stock=item["total_stock"]
            )
            for item in stats
        ]

    def get_best_selling_product_type(self) -> tuple:
        
        stats = self.get_inventory_sales_stats()
        if not stats:
            return "", 0
        
        best = stats[0]                                
        return best.product_type, best.total_sold

    def get_best_selling_platform(self) -> List[PlatformSalesStats]:
        
        customer_id = self._get_customer_id_filter()
        type_counts = self._order_repo.count_by_customer_type(customer_id)
        
        result = []
        for item in type_counts:
            result.append(PlatformSalesStats(
                platform=str(item["customer_type"]),
                total_sold=0,                              
                total_count=item["count"]
            ))
        
        return result

    def get_all_inventory_for_display(self) -> List[Inventory]:
        
        if not self._inventory_repo:
            return []
        return self._inventory_repo.find_all_inventory()
