import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Inventory
from enums import InventoryStatus
from database.connection import get_db


class InventoryRepositoryError(Exception):
    pass


class InventoryNotFoundError(InventoryRepositoryError):
    pass


class InventoryAlreadyExistsError(InventoryRepositoryError):
    pass


class InventoryRepository:
    def __init__(self):
        self._db = get_db()

    def _get_session(self) -> Session:
        return self._db.get_session()

    def create_inventory(self, inventory: Inventory) -> None:
        if not inventory.validate():
            raise ValueError("Invalid inventory data")
        
        if not inventory.product_id:
            inventory.product_id = str(uuid.uuid4())
        
        inventory.update_status()
        
        session = self._get_session()
        try:
            session.add(inventory)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_inventory_by_id(self, product_id: str) -> Inventory:
        session = self._get_session()
        try:
            inventory = session.query(Inventory).filter(
                Inventory.product_id == product_id
            ).first()
            if not inventory:
                raise InventoryNotFoundError(
                    f"Inventory with ID '{product_id}' not found"
                )
            return inventory
        finally:
            session.close()

    def get_inventory_by_name(self, product_name: str) -> Inventory:
        session = self._get_session()
        try:
            inventory = session.query(Inventory).filter(
                Inventory.product_name == product_name
            ).first()
            if not inventory:
                raise InventoryNotFoundError(
                    f"Inventory '{product_name}' not found"
                )
            return inventory
        finally:
            session.close()

    def update_inventory(self, inventory: Inventory) -> None:
        if not inventory.product_id:
            raise ValueError("Product ID is required")
        
        inventory.update_status()
        
        session = self._get_session()
        try:
            existing = session.query(Inventory).filter(
                Inventory.product_id == inventory.product_id
            ).first()
            if not existing:
                raise InventoryNotFoundError(
                    f"Inventory with ID '{inventory.product_id}' not found"
                )
            
            for key, value in inventory.__dict__.items():
                if not key.startswith('_') and key != 'product_id':
                    setattr(existing, key, value)
            
            session.commit()
        except InventoryNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_inventory(self, product_id: str) -> None:
        session = self._get_session()
        try:
            result = session.query(Inventory).filter(
                Inventory.product_id == product_id
            ).delete()
            if result == 0:
                raise InventoryNotFoundError(
                    f"Inventory with ID '{product_id}' not found"
                )
            session.commit()
        except InventoryNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_all_inventory(self) -> List[Inventory]:
        session = self._get_session()
        try:
            return session.query(Inventory).all()
        finally:
            session.close()

    def find_inventory_by_type(self, product_type: str) -> List[Inventory]:
        session = self._get_session()
        try:
            return session.query(Inventory).filter(
                Inventory.product_type == product_type
            ).all()
        finally:
            session.close()

    def find_inventory_by_id(self, product_id: str) -> List[Inventory]:
        session = self._get_session()
        try:
            return session.query(Inventory).filter(
                Inventory.product_id == product_id
            ).all()
        finally:
            session.close()

    def find_inventory_by_status(self, status: InventoryStatus) -> List[Inventory]:
        session = self._get_session()
        try:
            return session.query(Inventory).filter(
                Inventory.status == int(status)
            ).all()
        finally:
            session.close()

    def search_inventory(self, keyword: str) -> List[Inventory]:
        session = self._get_session()
        try:
            return session.query(Inventory).filter(
                (Inventory.product_name.like(f"%{keyword}%")) |
                (Inventory.product_type.like(f"%{keyword}%")) |
                (Inventory.manufacturer.like(f"%{keyword}%"))
            ).all()
        finally:
            session.close()

    def count(self) -> int:
        session = self._get_session()
        try:
            return session.query(Inventory).count()
        finally:
            session.close()

    def update_stock(self, product_id: str, quantity_change: int) -> None:
        session = self._get_session()
        try:
            inventory = session.query(Inventory).filter(
                Inventory.product_id == product_id
            ).first()
            if not inventory:
                raise InventoryNotFoundError(
                    f"Inventory with ID '{product_id}' not found"
                )
            
            inventory.stock_quantity += quantity_change
            if quantity_change < 0:
                inventory.sold_quantity -= quantity_change
            
            inventory.update_status()
            session.commit()
        except InventoryNotFoundError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_or_create_inventory(
        self,
        product_name: str,
        product_type: str,
        manufacturer: str,
        product_model: str = ""
    ) -> Inventory:
        session = self._get_session()
        try:
            inventory = session.query(Inventory).filter(
                Inventory.product_name == product_name
            ).first()
            
            if inventory:
                return inventory
            
            inventory = Inventory(
                product_id=str(uuid.uuid4()),
                product_name=product_name,
                product_type=product_type,
                manufacturer=manufacturer,
                product_model=product_model,
                stock_quantity=0,
                sold_quantity=0,
                status=int(InventoryStatus.NORMAL),
            )
            session.add(inventory)
            session.commit()
            return inventory
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_sales_by_product_type(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            results = session.query(
                Inventory.product_type,
                func.sum(Inventory.sold_quantity).label('total_sold'),
                func.sum(Inventory.stock_quantity).label('total_stock')
            ).group_by(Inventory.product_type).order_by(
                func.sum(Inventory.sold_quantity).desc()
            ).all()
            
            return [{
                "product_type": r[0],
                "total_sold": r[1] or 0,
                "total_stock": r[2] or 0,
            } for r in results]
        finally:
            session.close()
