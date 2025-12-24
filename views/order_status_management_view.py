from datetime import datetime
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from models import Order
from enums import OrderStatus, UserRole
from database import OrderRepository, InventoryRepository
from services import OrderService
from utils import get_service_runner


class OrderStatusManagementView(QWidget):
    back_to_main = pyqtSignal()
    permission_denied = pyqtSignal()

    def __init__(self, order_service: OrderService, user_service=None):
        super().__init__()
        self._order_service = order_service
        self._user_service = user_service
        self._order_repo = OrderRepository()
        self._inventory_repo = InventoryRepository()
        self._selected_orders: Dict[str, Order] = {}
        self._order_checkboxes: Dict[str, QCheckBox] = {}
        self._status_combos: Dict[str, QComboBox] = {}
        self._has_permission = self._check_permission()
        
        if not self._has_permission:
            self._setup_permission_denied_ui()
            return
        
        self._setup_ui()
        self._load_orders()

    def _setup_permission_denied_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        layout.addWidget(back_btn)
        
        layout.addStretch()
        label = QLabel("⚠️ 权限不足\n\n只有操作员及以上用户可以访问此页面")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #dc3545;")
        layout.addWidget(label)
        layout.addStretch()

    def _check_permission(self) -> bool:
        if not self._user_service:
            return False
        
        current_user = self._user_service.get_current_user()
        if not current_user:
            return False
        
        return current_user.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR]

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("📋 订单状态管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("按状态筛选:")
        filter_layout.addWidget(filter_label)
        
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("全部", None)
        for status in OrderStatus:
            if status != OrderStatus.UNKNOWN:
                self._filter_combo.addItem(str(status), status)
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_combo)
        
        filter_layout.addStretch()
        
        self._select_all_checkbox = QCheckBox("全选")
        self._select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        filter_layout.addWidget(self._select_all_checkbox)
        
        layout.addLayout(filter_layout)
        
        self._order_table = QTableWidget()
        self._order_table.setColumnCount(8)
        self._order_table.setHorizontalHeaderLabels([
            "选择", "订单号", "产品ID", "数量", "当前状态", "修改状态", "客户名", "下单时间"
        ])
        self._order_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._order_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._order_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._order_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self._order_table)
        
        batch_group = QGroupBox("批量修改状态")
        batch_layout = QHBoxLayout(batch_group)
        
        batch_label = QLabel("批量修改为:")
        batch_layout.addWidget(batch_label)
        
        self._batch_status_combo = QComboBox()
        for status in OrderStatus:
            if status != OrderStatus.UNKNOWN:
                self._batch_status_combo.addItem(str(status), status)
        batch_layout.addWidget(self._batch_status_combo)
        
        batch_btn = QPushButton("批量修改")
        batch_btn.clicked.connect(self._on_batch_update_clicked)
        batch_layout.addWidget(batch_btn)
        
        batch_layout.addStretch()
        
        layout.addWidget(batch_group)
        
        btn_layout = QHBoxLayout()
        
        single_update_btn = QPushButton("按单独选择的状态修改")
        single_update_btn.setFixedHeight(40)
        single_update_btn.setStyleSheet("background-color: #28a745; color: white;")
        single_update_btn.clicked.connect(self._on_single_update_clicked)
        btn_layout.addWidget(single_update_btn)
        
        layout.addLayout(btn_layout)

    def _load_orders(self, status_filter: OrderStatus = None):
        runner = get_service_runner()
        if status_filter is not None:
            runner.run(
                self._order_service.get_orders_by_status,
                args=(status_filter,),
                on_success=self._populate_order_table,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"加载订单失败: {e}")
            )
        else:
            runner.run(
                self._order_service.get_all_orders,
                on_success=self._populate_order_table,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"加载订单失败: {e}")
            )

    def _populate_order_table(self, orders: List[Order]):
        self._order_table.setRowCount(len(orders))
        self._order_checkboxes.clear()
        self._status_combos.clear()
        self._selected_orders.clear()
        
        if not orders:
            self._order_table.setRowCount(1)
            empty_item = QTableWidgetItem("暂无订单")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._order_table.setItem(0, 0, empty_item)
            self._order_table.setSpan(0, 0, 1, 8)
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
            
            checkbox.stateChanged.connect(lambda state, o=order: self._on_checkbox_changed(o, state))
            
            order_id_item = QTableWidgetItem(order.order_id or "")
            self._order_table.setItem(row, 1, order_id_item)
            
            product_id_item = QTableWidgetItem(order.product_id or "")
            self._order_table.setItem(row, 2, product_id_item)
            
            quantity_item = QTableWidgetItem(str(order.quantity))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._order_table.setItem(row, 3, quantity_item)
            
            status_item = QTableWidgetItem(str(OrderStatus(order.status)))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._order_table.setItem(row, 4, status_item)
            
            status_combo = QComboBox()
            for status in OrderStatus:
                if status != OrderStatus.UNKNOWN:
                    status_combo.addItem(str(status), status)
            for i in range(status_combo.count()):
                if status_combo.itemData(i) == OrderStatus(order.status):
                    status_combo.setCurrentIndex(i)
                    break
            self._order_table.setCellWidget(row, 5, status_combo)
            self._status_combos[order.hash] = status_combo
            
            customer_item = QTableWidgetItem(order.customer_name or "")
            self._order_table.setItem(row, 6, customer_item)
            
            order_time_str = ""
            if order.order_time:
                order_time_str = order.order_time.strftime("%Y-%m-%d %H:%M")
            order_time_item = QTableWidgetItem(order_time_str)
            self._order_table.setItem(row, 7, order_time_item)
            
            order_id_item.setData(Qt.ItemDataRole.UserRole, order)

    def _on_filter_changed(self, index):
        status = self._filter_combo.itemData(index)
        self._load_orders(status)

    def _on_select_all_changed(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        for checkbox in self._order_checkboxes.values():
            checkbox.setChecked(is_checked)

    def _on_checkbox_changed(self, order: Order, state: int):
        if state == Qt.CheckState.Checked.value:
            self._selected_orders[order.hash] = order
        else:
            if order.hash in self._selected_orders:
                del self._selected_orders[order.hash]

    def _on_batch_update_clicked(self):
        if not self._selected_orders:
            QMessageBox.warning(self, "错误", "请选择至少一个订单")
            return
        
        new_status = self._batch_status_combo.currentData()
        
        reply = QMessageBox.question(
            self, "确认批量修改",
            f"确定要将选中的 {len(self._selected_orders)} 个订单状态修改为 {str(new_status)} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            orders_to_update = [(order, new_status) for order in self._selected_orders.values()]
            
            def do_batch_update():
                updated_count = 0
                for order, status in orders_to_update:
                    order.status = int(status)
                    self._order_repo.update_order(order)
                    updated_count += 1
                return updated_count
            
            runner = get_service_runner()
            runner.run(
                do_batch_update,
                on_success=self._on_batch_update_success,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"批量修改状态失败: {e}")
            )
    
    def _on_batch_update_success(self, updated_count):
        QMessageBox.information(
            self, "修改成功",
            f"已成功修改 {updated_count} 个订单的状态。"
        )
        
        self._selected_orders.clear()
        self._select_all_checkbox.setChecked(False)
        self._load_orders(self._filter_combo.currentData())

    def _on_single_update_clicked(self):
        if not self._selected_orders:
            QMessageBox.warning(self, "错误", "请选择至少一个订单")
            return
        
        reply = QMessageBox.question(
            self, "确认修改",
            f"确定要按照每个订单的选择修改 {len(self._selected_orders)} 个订单的状态吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            orders_to_update = []
            for order_hash, order in self._selected_orders.items():
                if order_hash in self._status_combos:
                    new_status = self._status_combos[order_hash].currentData()
                    orders_to_update.append((order, new_status))
            
            def do_single_update():
                updated_count = 0
                for order, status in orders_to_update:
                    order.status = int(status)
                    self._order_repo.update_order(order)
                    updated_count += 1
                return updated_count
            
            runner = get_service_runner()
            runner.run(
                do_single_update,
                on_success=self._on_single_update_success,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"修改状态失败: {e}")
            )
    
    def _on_single_update_success(self, updated_count):
        QMessageBox.information(
            self, "修改成功",
            f"已成功修改 {updated_count} 个订单的状态。"
        )
        
        self._selected_orders.clear()
        self._select_all_checkbox.setChecked(False)
        self._load_orders(self._filter_combo.currentData())
