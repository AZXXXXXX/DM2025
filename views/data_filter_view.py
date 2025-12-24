from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate

from services import OrderService
from enums import OrderStatus, CustomerType
from utils import get_service_runner


class DataFilterView(QWidget):
    back_to_main = pyqtSignal()

    def __init__(self, order_service: OrderService):
        super().__init__()
        self._order_service = order_service
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("🔍 筛选订单数据")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        filter_layout = self._create_filter_form()
        layout.addLayout(filter_layout)
        
        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self._on_search_clicked)
        layout.addWidget(search_btn)
        
        self._table = QTableWidget()
        self._table.setColumnCount(12)
        self._table.setHorizontalHeaderLabels([
            "客户类型", "客户名", "销售员", "订单号", "运单号", "状态",
            "下单时间", "付款时间", "发货截止", "产品ID", "数量", "退货处理号"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)
        
        self._result_label = QLabel("共 0 条记录")
        layout.addWidget(self._result_label)

    def _create_filter_form(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        order_id_layout = QVBoxLayout()
        order_id_layout.addWidget(QLabel("订单号:"))
        self._order_id_entry = QLineEdit()
        self._order_id_entry.setPlaceholderText("订单号")
        order_id_layout.addWidget(self._order_id_entry)
        layout.addLayout(order_id_layout)
        
        customer_layout = QVBoxLayout()
        customer_layout.addWidget(QLabel("客户名:"))
        self._customer_entry = QLineEdit()
        self._customer_entry.setPlaceholderText("客户名")
        customer_layout.addWidget(self._customer_entry)
        layout.addLayout(customer_layout)

        sales_layout = QVBoxLayout()
        sales_layout.addWidget(QLabel("销售员:"))
        self._sales_entry = QLineEdit()
        self._sales_entry.setPlaceholderText("销售员")
        sales_layout.addWidget(self._sales_entry)
        layout.addLayout(sales_layout)
        
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        self._status_combo = QComboBox()
        self._status_combo.addItem("全部", None)
        for status in OrderStatus:
            if status != OrderStatus.UNKNOWN:
                self._status_combo.addItem(str(status), status)
        status_layout.addWidget(self._status_combo)
        layout.addLayout(status_layout)
        
        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("客户类型:"))
        self._type_combo = QComboBox()
        self._type_combo.addItem("全部", None)
        for ct in CustomerType:
            if ct != CustomerType.UNKNOWN:
                self._type_combo.addItem(str(ct), ct)
        type_layout.addWidget(self._type_combo)
        layout.addLayout(type_layout)
        
        return layout

    def _on_search_clicked(self):
        order_id = self._order_id_entry.text().strip()
        customer_name = self._customer_entry.text().strip()
        sales = self._sales_entry.text().strip()
        
        status = self._status_combo.currentText()
        customer_type = self._type_combo.currentText()
        
        def do_search():
            return self._order_service.get_orders_by_filter(
                order_id=order_id,
                customer_name=customer_name,
                sales=sales,
                status=OrderStatus.from_string(status),
                customer_type=CustomerType.from_string(customer_type)
            )
        
        runner = get_service_runner()
        runner.run(
            do_search,
            on_success=self._on_search_success,
            on_error=lambda e: QMessageBox.critical(self, "错误", f"搜索失败: {e}")
        )
    
    def _on_search_success(self, orders):
        self._populate_table(orders)
        self._result_label.setText(f"共 {len(orders)} 条记录")

    def _populate_table(self, orders):
        self._table.setRowCount(0)
        
        for order in orders:
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            data = order.to_array()
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, col, item)
