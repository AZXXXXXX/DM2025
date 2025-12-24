import uuid
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QFrame, QMessageBox, QScrollArea,
    QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from services import OrderService
from database import InventoryRepository
from models import Order
from enums import OrderStatus, CustomerType, InventoryStatus, UserRole
from utils import get_service_runner


class PlaceOrderView(QWidget):
    back_to_main = pyqtSignal()

    def __init__(self, order_service: OrderService, user_service=None, inventory_repo=None, show_payment_callback: Optional[Callable] = None):
        super().__init__()
        self._order_service = order_service
        self._user_service = user_service
        self._inventory_repo = inventory_repo or InventoryRepository()
        self._product_quantities: Dict[str, QSpinBox] = {}
        self._is_customer_user = self._check_is_customer_user()
        self._show_payment_callback = show_payment_callback
        self._pending_order_products: Optional[Dict] = None
        self._pending_order_info: Optional[Dict] = None
        self._setup_ui()
        self._load_products()

    def _check_is_customer_user(self) -> bool:
        if self._user_service and self._user_service.is_logged_in():
            current_user = self._user_service.get_current_user()
            return current_user.role == UserRole.CUSTOMER
        return False

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("🛒 下单")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        self._customer_type_combo = QComboBox()
        for ct in CustomerType:
            if ct != CustomerType.UNKNOWN:
                self._customer_type_combo.addItem(str(ct), ct)
        
        if not self._is_customer_user:
            type_layout = QHBoxLayout()
            type_label = QLabel("客户类型:")
            type_layout.addWidget(type_label)
            type_layout.addWidget(self._customer_type_combo)
            type_layout.addStretch()
            layout.addLayout(type_layout)
        
        instructions = QLabel("请在下表中选择要购买的产品并填写数量:")
        instructions.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(instructions)
        
        self._product_table = QTableWidget()
        self._product_table.setColumnCount(7)
        self._product_table.setHorizontalHeaderLabels([
            "品牌", "产品名称", "产品型号", "库存数量", "状态", "预计补货时间", "购买数量"
        ])
        self._product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._product_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._product_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._product_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._product_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._product_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self._product_table)
        
        submit_btn = QPushButton("提交订单")
        submit_btn.setFixedHeight(40)
        submit_btn.clicked.connect(self._on_submit_clicked)
        layout.addWidget(submit_btn)

    def _load_products(self):
        runner = get_service_runner()
        runner.run(
            self._inventory_repo.find_all_inventory,
            on_success=self._populate_products_table,
            on_error=lambda e: QMessageBox.critical(self, "错误", f"加载产品列表失败: {e}")
        )
    
    def _populate_products_table(self, items):
        available_items = [
            item for item in items 
            if item.status != InventoryStatus.OFF_SHELF
        ]
        
        if not available_items:
            self._product_table.setRowCount(1)
            empty_item = QTableWidgetItem("暂无可购买产品")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._product_table.setItem(0, 0, empty_item)
            self._product_table.setSpan(0, 0, 1, 6)
            return
        
        self._product_table.setRowCount(len(available_items))
        
        for row, item in enumerate(available_items):
            brand_item = QTableWidgetItem(item.manufacturer or "")
            self._product_table.setItem(row, 0, brand_item)

            name_item = QTableWidgetItem(item.product_name or "")
            self._product_table.setItem(row, 1, name_item)
            
            model_item = QTableWidgetItem(item.product_model or "")
            self._product_table.setItem(row, 2, model_item)
            
            stock_item = QTableWidgetItem(str(item.stock_quantity))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._product_table.setItem(row, 3, stock_item)
            
            status_text = str(InventoryStatus(item.status))
            if item.stock_quantity < 0:
                status_text = "缺货"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._product_table.setItem(row, 4, status_item)
            
            if item.expected_arrival:
                arrival_text = item.expected_arrival.strftime("%Y-%m-%d")
            else:
                arrival_text = "-"
            arrival_item = QTableWidgetItem(arrival_text)
            arrival_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._product_table.setItem(row, 5, arrival_item)
            
            quantity_spin = QSpinBox()
            is_orderable = (item.status == InventoryStatus.NORMAL and item.stock_quantity > 0)
            if is_orderable:
                quantity_spin.setRange(0, max(item.stock_quantity, 0))
                quantity_spin.setValue(0)
                quantity_spin.setEnabled(True)
            else:
                quantity_spin.setRange(0, 0)
                quantity_spin.setValue(0)
                quantity_spin.setEnabled(False)
            self._product_table.setCellWidget(row, 6, quantity_spin)
            
            self._product_quantities[item.product_id] = quantity_spin
            
            name_item.setData(Qt.ItemDataRole.UserRole, item.product_id)

    def _on_submit_clicked(self):
        selected_products = {}
        
        for row in range(self._product_table.rowCount()):
            name_item = self._product_table.item(row, 1)
            if not name_item:
                continue
            
            product_id = name_item.data(Qt.ItemDataRole.UserRole)
            if not product_id:
                continue
            
            quantity_spin = self._product_table.cellWidget(row, 6)
            if quantity_spin and quantity_spin.value() > 0:
                selected_products[product_id] = quantity_spin.value()
        
        if not selected_products:
            QMessageBox.warning(self, "错误", "请选择至少一个产品")
            return
        
        self._pending_order_products = selected_products
        
        runner = get_service_runner()
        runner.run(
            self._validate_stock_async,
            args=(selected_products,),
            on_success=self._on_stock_validated,
            on_error=self._on_stock_validation_error
        )
    
    def _on_stock_validation_error(self, error):
        self._pending_order_products = None
        self._pending_order_info = None
        QMessageBox.warning(self, "错误", f"产品验证失败: {error}")
    
    def _validate_stock_async(self, selected_products):
        validation_results = {}
        for product_id, quantity in selected_products.items():
            inventory = self._inventory_repo.get_inventory_by_id(product_id)
            validation_results[product_id] = {
                'inventory': inventory,
                'quantity': quantity,
                'valid': inventory.stock_quantity >= quantity
            }
        return validation_results
    
    def _on_stock_validated(self, validation_results):
        for product_id, result in validation_results.items():
            if not result['valid']:
                inventory = result['inventory']
                self._pending_order_products = None
                QMessageBox.warning(
                    self, "错误",
                    f"产品 {inventory.product_name} 库存不足，"
                    f"当前库存: {inventory.stock_quantity}，需要: {result['quantity']}"
                )
                return
        
        self._create_orders_async()
    
    def _create_orders_async(self):
        selected_products = self._pending_order_products
        
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order_time = datetime.now()
        ship_deadline = order_time + timedelta(days=3)
        
        customer_name = ""
        sales = "在线下单"
        
        if self._is_customer_user:
            customer_type = CustomerType.ONLINE_RETAIL
        else:
            customer_type = self._customer_type_combo.currentData()
        
        if self._user_service and self._user_service.is_logged_in():
            current_user = self._user_service.get_current_user()
            customer_name = current_user.display_name
            
            if current_user.role == UserRole.OPERATOR:
                sales = current_user.display_name
            elif current_user.role == UserRole.VIEWER:
                customer_type = CustomerType.UNKNOWN
        
        self._pending_order_info = {
            'order_id': order_id,
            'order_time': order_time,
            'ship_deadline': ship_deadline,
            'customer_type': int(customer_type),
            'customer_name': customer_name,
            'sales': sales,
            'selected_products': selected_products
        }
        
        runner = get_service_runner()
        runner.run(
            self._create_orders_in_thread,
            args=(self._pending_order_info,),
            on_success=self._on_orders_created,
            on_error=self._on_order_creation_error
        )
    
    def _on_order_creation_error(self, error):
        self._pending_order_products = None
        self._pending_order_info = None
        QMessageBox.critical(self, "错误", f"创建订单失败: {error}")
    
    def _create_orders_in_thread(self, order_info):
        created_orders = 0
        stock_update_failures = 0
        
        for product_id, quantity in order_info['selected_products'].items():
            order = Order(
                customer_type=int(order_info['customer_type']),
                customer_name=order_info['customer_name'],
                sales=order_info['sales'],
                order_id=order_info['order_id'],
                product_id=product_id,
                quantity=quantity,
                order_time=order_info['order_time'],
                ship_deadline=order_info['ship_deadline'],
                status=int(OrderStatus.PENDING_PAYMENT),
            )
            
            self._order_service.create_order(order)

            try:
                self._inventory_repo.update_stock(product_id, -quantity)
            except Exception:
                stock_update_failures += 1
            
            created_orders += 1
        
        return {
            'order_id': order_info['order_id'],
            'order_time': order_info['order_time'],
            'created_orders': created_orders,
            'stock_update_failures': stock_update_failures
        }
    
    def _on_orders_created(self, result):
        self._pending_order_products = None
        self._pending_order_info = None
        
        order_id = result['order_id']
        order_time = result['order_time']
        created_orders = result['created_orders']
        stock_update_failures = result['stock_update_failures']
        
        if self._show_payment_callback:
            self._show_payment_callback(order_id, created_orders, order_time)
        else:
            success_message = (
                f"订单号: {order_id}\n"
                f"共 {created_orders} 个产品\n"
                f"下单时间: {order_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"请等待发货"
            )
            
            if stock_update_failures > 0:
                success_message += f"\n\n注意: {stock_update_failures} 个产品库存更新失败"
            
            QMessageBox.information(self, "下单成功", success_message)

            self._reset_form()

    def _reset_form(self):
        for spin in self._product_quantities.values():
            spin.setValue(0)
        
        self._product_quantities.clear()
        self._load_products()
