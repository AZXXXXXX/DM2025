

from datetime import datetime
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from models import Order, ReturnRequest, ReturnStatus
from enums import OrderStatus, ReturnReason, UserRole
from database import OrderRepository, InventoryRepository
from services import OrderService
from utils import get_service_runner


class ReturnRequestView(QWidget):
    
    
    back_to_main = pyqtSignal()

    def __init__(self, order_service: OrderService, user_service=None):
        
        super().__init__()
        self._order_service = order_service
        self._user_service = user_service
        self._order_repo = OrderRepository()
        self._inventory_repo = InventoryRepository()
        self._selected_orders: Dict[str, Order] = {}                 
        self._order_checkboxes: Dict[str, QCheckBox] = {}                     
        
        self._setup_ui()
        self._load_orders()

    def _setup_ui(self):
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
                 
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("📦 退货申请")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
                   
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
                      
        instructions = QLabel("请选择需要申请退货的订单，并选择退货原因:")
        instructions.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(instructions)
        
                     
        self._order_table = QTableWidget()
        self._order_table.setColumnCount(7)
        self._order_table.setHorizontalHeaderLabels([
            "选择", "订单号", "产品ID", "数量", "下单时间", "状态", "客户名"
        ])
        self._order_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._order_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._order_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self._order_table)
        
                                 
        reason_group = QGroupBox("退货原因")
        reason_layout = QHBoxLayout(reason_group)
        
        reason_label = QLabel("请选择退货原因:")
        reason_layout.addWidget(reason_label)
        
        self._reason_combo = QComboBox()
        for reason_str in ReturnReason.get_all_reasons():
            self._reason_combo.addItem(reason_str)
        reason_layout.addWidget(self._reason_combo)
        
        reason_layout.addStretch()
        
        layout.addWidget(reason_group)
        
                       
        submit_btn = QPushButton("提交退货申请")
        submit_btn.setFixedHeight(40)
        submit_btn.setStyleSheet("background-color: #007bff; color: white;")
        submit_btn.clicked.connect(self._on_submit_clicked)
        layout.addWidget(submit_btn)

    def _load_orders(self):
        
        try:
                                                       
            orders = self._order_service.get_all_orders()
            
                                                                  
                                                              
            filtered_orders = []
            for order in orders:
                                                                                      
                                                                                    
                if getattr(order, 'return_applied', False) and order.status == OrderStatus.RETURN_REJECTED:
                    continue
                                                                           
                if order.status in [OrderStatus.COMPLETED, OrderStatus.PENDING_RECEIVE]:
                    filtered_orders.append(order)
            
            self._populate_order_table(filtered_orders)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载订单失败: {e}")

    def _populate_order_table(self, orders: List[Order]):
        
        self._order_table.setRowCount(len(orders))
        self._order_checkboxes.clear()
        
        if not orders:
            self._order_table.setRowCount(1)
            empty_item = QTableWidgetItem("暂无可申请退货的订单")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._order_table.setItem(0, 0, empty_item)
            self._order_table.setSpan(0, 0, 1, 7)
            return
        
        for row, order in enumerate(orders):
                      
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self._order_table.setCellWidget(row, 0, checkbox_widget)
            self._order_checkboxes[order.hash] = checkbox
            
                                   
            checkbox.setProperty("order_hash", order.hash)
            checkbox.stateChanged.connect(lambda state, o=order: self._on_checkbox_changed(o, state))
            
                      
            order_id_item = QTableWidgetItem(order.order_id or "")
            self._order_table.setItem(row, 1, order_id_item)
            
                        
            product_id_item = QTableWidgetItem(order.product_id or "")
            self._order_table.setItem(row, 2, product_id_item)
            
                      
            quantity_item = QTableWidgetItem(str(order.quantity))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._order_table.setItem(row, 3, quantity_item)
            
                        
            order_time_str = ""
            if order.order_time:
                order_time_str = order.order_time.strftime("%Y-%m-%d %H:%M")
            order_time_item = QTableWidgetItem(order_time_str)
            self._order_table.setItem(row, 4, order_time_item)
            
                    
            status_item = QTableWidgetItem(str(OrderStatus(order.status)))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._order_table.setItem(row, 5, status_item)
            
                           
            customer_item = QTableWidgetItem(order.customer_name or "")
            self._order_table.setItem(row, 6, customer_item)
            
                                                     
            order_id_item.setData(Qt.ItemDataRole.UserRole, order)

    def _on_checkbox_changed(self, order: Order, state: int):
        
        if state == Qt.CheckState.Checked.value:
            self._selected_orders[order.hash] = order
        else:
            if order.hash in self._selected_orders:
                del self._selected_orders[order.hash]

    def _on_submit_clicked(self):
        
        if not self._selected_orders:
            QMessageBox.warning(self, "错误", "请选择至少一个订单")
            return
        
        reason_str = self._reason_combo.currentText()
        reason = ReturnReason.from_string(reason_str)
        
        reply = QMessageBox.question(
            self, "确认提交",
            f"确定要为选中的 {len(self._selected_orders)} 个订单申请退货吗？\n"
            f"退货原因: {reason_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            orders_to_update = list(self._selected_orders.values())
            
            def do_return_request():
                updated_count = 0
                for order in orders_to_update:
                                                            
                    order.status = int(OrderStatus.RETURN_APPLYING)
                    order.return_applied = True
                    self._order_repo.update_order(order)
                    updated_count += 1
                return updated_count
            
            runner = get_service_runner()
            runner.run(
                do_return_request,
                on_success=self._on_return_request_success,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"提交退货申请失败: {e}")
            )
    
    def _on_return_request_success(self, updated_count):
        
        QMessageBox.information(
            self, "申请成功",
            f"已成功提交 {updated_count} 个订单的退货申请。\n"
            f"请等待审核。"
        )
        
                       
        self._selected_orders.clear()
        self._load_orders()
