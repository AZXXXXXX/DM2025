

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
import math

from sqlalchemy import func, and_, or_, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Order
from enums import OrderStatus, CustomerType
from database.connection import get_db


class OrderRepository:
    
    
    PAGE_SIZE = 50

    def __init__(self):
        
        self._db = get_db()

    def _get_session(self) -> Session:
        
        return self._db.get_session()

    def create_order(self, order: Order) -> None:
        
        if not order.check_entity():
            raise ValueError("Invalid order data")
        
        order.generate_hash()
        
        session = self._get_session()
        try:
                                                  
            existing = session.query(Order).filter(Order.hash == order.hash).first()
            if existing:
                                       
                for key, value in order.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
                session.commit()
            else:
                session.add(order)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find(
        self,
        order_id: str = "",
        customer_name: str = "",
        sales: str = "",
        status: Optional[OrderStatus] = None,
        customer_type: Optional[CustomerType] = None,
        ship_deadline: Optional[datetime] = None
    ) -> List[Order]:
        
        if not any([order_id, customer_name, sales, status is not None, 
                   customer_type is not None, ship_deadline]):
            return self.find_all()
        
        session = self._get_session()
        try:
            query = session.query(Order)
            
            if order_id:
                query = query.filter(Order.order_id.like(f"%{order_id}%"))
            if customer_name:
                query = query.filter(Order.customer_name.like(f"%{customer_name}%"))
            if sales:
                query = query.filter(Order.sales == sales)
            if status is not None and status != OrderStatus.UNKNOWN:
                query = query.filter(Order.status == int(status))
            if customer_type is not None and customer_type != CustomerType.UNKNOWN:
                query = query.filter(Order.customer_type == int(customer_type))
            if ship_deadline:
                query = query.filter(Order.ship_deadline == ship_deadline)
            
                             
            total_count = query.count()
            if total_count == 0:
                return []
            
            orders = []
            total_pages = math.ceil(total_count / self.PAGE_SIZE)
            
            for page in range(total_pages):
                page_orders = query.offset(page * self.PAGE_SIZE).limit(self.PAGE_SIZE).all()
                orders.extend(page_orders)
            
            return orders
        finally:
            session.close()

    def find_all(self) -> List[Order]:
        
        session = self._get_session()
        try:
            total_count = session.query(Order).count()
            if total_count == 0:
                return []
            
            orders = []
            total_pages = math.ceil(total_count / self.PAGE_SIZE)
            
            for page in range(total_pages):
                page_orders = session.query(Order).offset(page * self.PAGE_SIZE).limit(self.PAGE_SIZE).all()
                orders.extend(page_orders)
            
            return orders
        finally:
            session.close()

    def find_by_order_id(self, order_id: str) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.order_id == order_id).all()
        finally:
            session.close()

    def find_by_product_id(self, product_id: str) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.product_id == product_id).all()
        finally:
            session.close()

    def find_by_status(self, status: OrderStatus) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.status == int(status)).all()
        finally:
            session.close()

    def find_by_customer_type(self, customer_type: CustomerType) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.customer_type == int(customer_type)).all()
        finally:
            session.close()

    def find_by_ship_deadline(self, ship_deadline: datetime) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.ship_deadline == ship_deadline).all()
        finally:
            session.close()

    def find_by_sales(self, sales: str) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.sales == sales).all()
        finally:
            session.close()

    def find_by_customer_name(self, customer_name: str) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(
                Order.customer_name.like(f"%{customer_name}%")
            ).all()
        finally:
            session.close()

    def find_by_customer_id(self, customer_id: str) -> List[Order]:
        
        session = self._get_session()
        try:
            return session.query(Order).filter(Order.customer_id == customer_id).all()
        finally:
            session.close()

    def update_order(self, order: Order) -> None:
        
        if not order.check_entity():
            raise ValueError("Invalid order data")
        
        session = self._get_session()
        try:
            existing = session.query(Order).filter(Order.hash == order.hash).first()
            if not existing:
                raise ValueError("Order not found")
            
            for key, value in order.__dict__.items():
                if not key.startswith('_') and key != 'hash':
                    setattr(existing, key, value)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_order(self, order: Order) -> None:
        
        session = self._get_session()
        try:
            session.query(Order).filter(Order.hash == order.hash).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def count(self) -> int:
        
        session = self._get_session()
        try:
            return session.query(Order).count()
        finally:
            session.close()

    def count_by_status(self, customer_id: str = "") -> List[Dict[str, Any]]:
        
        session = self._get_session()
        try:
            query = session.query(
                Order.status,
                func.count(Order.hash).label('count')
            )
            
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            
            results = query.group_by(Order.status).all()
            
            return [{"status": OrderStatus(r[0]), "count": r[1]} for r in results]
        finally:
            session.close()

    def count_by_customer_type(self, customer_id: str = "") -> List[Dict[str, Any]]:
        
        session = self._get_session()
        try:
            query = session.query(
                Order.customer_type,
                func.count(Order.hash).label('count')
            )
            
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            
            results = query.group_by(Order.customer_type).all()
            
            return [{"customer_type": CustomerType(r[0]), "count": r[1]} for r in results]
        finally:
            session.close()

    def count_by_sales(self, customer_id: str = "") -> List[Dict[str, Any]]:
        
        session = self._get_session()
        try:
            query = session.query(
                Order.sales,
                func.count(Order.hash).label('count')
            ).filter(Order.sales != '')
            
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            
            results = query.group_by(Order.sales).all()
            
            return [{"sales": r[0], "count": r[1]} for r in results]
        finally:
            session.close()

    def find_nearing_deadline(self, days: int, customer_id: str = "") -> List[Order]:
        
        session = self._get_session()
        try:
            now = datetime.now()
            start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_target_day = start_of_today + timedelta(days=days)
            
            query = session.query(Order).filter(
                Order.status != OrderStatus.COMPLETED,
                Order.ship_deadline >= start_of_today,
                Order.ship_deadline < end_of_target_day
            ).order_by(Order.ship_deadline)
            
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            
            return query.all()
        finally:
            session.close()

    def get_dashboard_counts(self, customer_id: str = "") -> Dict[str, Any]:
        
        session = self._get_session()
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            three_days_later = today + timedelta(days=3)
            
            pending_statuses = OrderStatus.get_pending_statuses()
            
                         
            total_query = session.query(func.count(Order.hash))
            if customer_id:
                total_query = total_query.filter(Order.customer_id == customer_id)
            total = total_query.scalar() or 0
            
                           
            pending_query = session.query(func.count(Order.hash)).filter(
                Order.status.in_([int(s) for s in pending_statuses])
            )
            if customer_id:
                pending_query = pending_query.filter(Order.customer_id == customer_id)
            pending = pending_query.scalar() or 0
            
                             
            completed_query = session.query(func.count(Order.hash)).filter(
                Order.status == int(OrderStatus.COMPLETED)
            )
            if customer_id:
                completed_query = completed_query.filter(Order.customer_id == customer_id)
            completed = completed_query.scalar() or 0
            
                                 
            near_deadline_query = session.query(func.count(Order.hash)).filter(
                Order.status.notin_([int(OrderStatus.COMPLETED), int(OrderStatus.PAUSED)]),
                Order.ship_deadline >= today,
                Order.ship_deadline < three_days_later
            )
            if customer_id:
                near_deadline_query = near_deadline_query.filter(Order.customer_id == customer_id)
            near_deadline = near_deadline_query.scalar() or 0
            
            return {
                "total_orders": total,
                "pending_orders": pending,
                "completed_orders": completed,
                "near_deadline_orders": near_deadline,
            }
        finally:
            session.close()

    def get_deadline_stats(self, customer_id: str = "") -> Dict[str, int]:
        
        session = self._get_session()
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            day_after_tomorrow = today + timedelta(days=2)
            in_4_days = today + timedelta(days=4)
            in_8_days = today + timedelta(days=8)
            
            def get_count(start, end=None, is_overdue=False):
                query = session.query(func.count(Order.hash)).filter(
                    Order.status.notin_([OrderStatus.COMPLETED, OrderStatus.PAUSED])
                )
                if customer_id:
                    query = query.filter(Order.customer_id == customer_id)
                
                if is_overdue:
                    query = query.filter(Order.ship_deadline < start)
                elif end:
                    query = query.filter(
                        Order.ship_deadline >= start,
                        Order.ship_deadline < end
                    )
                else:
                    query = query.filter(Order.ship_deadline >= start)
                
                return query.scalar() or 0
            
            return {
                "已逾期": get_count(today, is_overdue=True),
                "今日截止": get_count(today, tomorrow),
                "明日截止": get_count(tomorrow, day_after_tomorrow),
                "3日内截止": get_count(day_after_tomorrow, in_4_days),
                "7日内截止": get_count(in_4_days, in_8_days),
                "7日以上": get_count(in_8_days),
            }
        finally:
            session.close()

    def find_pending_orders_sorted(self, customer_id: str = "") -> List[Order]:
        
        session = self._get_session()
        try:
            query = session.query(Order).filter(
                Order.status.notin_([int(OrderStatus.COMPLETED), int(OrderStatus.PAUSED)])
            ).order_by(Order.ship_deadline)
            
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            
                             
            total_count = query.count()
            if total_count == 0:
                return []
            
            orders = []
            total_pages = math.ceil(total_count / self.PAGE_SIZE)
            
            for page in range(total_pages):
                page_orders = query.offset(page * self.PAGE_SIZE).limit(self.PAGE_SIZE).all()
                orders.extend(page_orders)
            
            return orders
        finally:
            session.close()
