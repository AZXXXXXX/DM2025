import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor

from models import Order
from enums import OrderStatus
from database import OrderRepository, InventoryRepository
from utils import get_service_runner


class PaymentView(QWidget):
    payment_completed = pyqtSignal()
    payment_cancelled = pyqtSignal()
    back_to_main = pyqtSignal()

    def __init__(
        self,
        order_id: str,
        total_products: int,
        order_time: datetime,
        order_service=None,
        inventory_repo=None
    ):
        super().__init__()
        self._order_id = order_id
        self._total_products = total_products
        self._order_time = order_time
        self._order_service = order_service
        self._order_repo = OrderRepository()
        self._inventory_repo = inventory_repo or InventoryRepository()
        
        self._cancel_timer: Optional[QTimer] = None
        self._countdown_timer: Optional[QTimer] = None
        self._remaining_seconds = 30 * 60
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("💳 订单支付")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        order_id_label = QLabel(f"订单号: {self._order_id}")
        order_id_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(order_id_label)
        
        products_label = QLabel(f"商品数量: {self._total_products} 件")
        products_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(products_label)
        
        time_label = QLabel(f"下单时间: {self._order_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        
        qr_frame = QFrame()
        qr_frame.setFrameShape(QFrame.Shape.Box)
        qr_frame.setStyleSheet("background-color: white; padding: 20px;")
        qr_layout = QVBoxLayout(qr_frame)
        
        qr_title = QLabel("扫码支付")
        qr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_title.setStyleSheet("font-size: 14px; color: gray;")
        qr_layout.addWidget(qr_title)
        
        self._qr_label = QLabel()
        self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_label.setFixedSize(200, 200)
        self._generate_qr_code()
        qr_layout.addWidget(self._qr_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(qr_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._countdown_label = QLabel(f"剩余支付时间: 30:00")
        self._countdown_label.setStyleSheet("font-size: 14px; color: #ff6600;")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._countdown_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_payment_btn = QPushButton("取消付款")
        cancel_payment_btn.setFixedHeight(40)
        cancel_payment_btn.setStyleSheet("background-color: #ffc107; color: black;")
        cancel_payment_btn.clicked.connect(self._on_cancel_payment_clicked)
        btn_layout.addWidget(cancel_payment_btn)
        
        cancel_order_btn = QPushButton("取消订单")
        cancel_order_btn.setFixedHeight(40)
        cancel_order_btn.setStyleSheet("background-color: #dc3545; color: white;")
        cancel_order_btn.clicked.connect(self._on_cancel_order_clicked)
        btn_layout.addWidget(cancel_order_btn)
        
        complete_btn = QPushButton("我已完成支付")
        complete_btn.setFixedHeight(40)
        complete_btn.setStyleSheet("background-color: #28a745; color: white;")
        complete_btn.clicked.connect(self._on_payment_completed_clicked)
        btn_layout.addWidget(complete_btn)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        self._start_countdown()

    def _generate_qr_code(self):
        qr_data = f"{self._order_id}:{self._total_products}:{self._order_time.isoformat()}"
        hash_value = hashlib.md5(qr_data.encode()).hexdigest()
        
        size = 200
        cell_size = 10
        grid_size = size // cell_size
        
        image = QImage(size, size, QImage.Format.Format_RGB32)
        image.fill(QColor(255, 255, 255))
        
        painter = QPainter(image)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0))
        
        for i in range(grid_size):
            for j in range(grid_size):
                idx = (i * grid_size + j) % len(hash_value)
                if int(hash_value[idx], 16) % 2 == 1:
                    painter.drawRect(j * cell_size, i * cell_size, cell_size, cell_size)
        
        marker_size = 3 * cell_size
        corners = [(0, 0), (0, size - marker_size), (size - marker_size, 0)]
        for x, y in corners:
            painter.fillRect(x, y, marker_size, marker_size, QColor(0, 0, 0))
            painter.fillRect(x + cell_size, y + cell_size, cell_size, cell_size, QColor(255, 255, 255))
        
        painter.end()
        
        pixmap = QPixmap.fromImage(image)
        self._qr_label.setPixmap(pixmap)

    def _start_countdown(self):
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_countdown)
        self._countdown_timer.start(1000)

    def _update_countdown(self):
        self._remaining_seconds -= 1
        
        if self._remaining_seconds <= 0:
            self._countdown_timer.stop()
            self._auto_cancel_order()
            return
        
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        self._countdown_label.setText(f"剩余支付时间: {minutes:02d}:{seconds:02d}")
        
        if self._remaining_seconds < 5 * 60:
            self._countdown_label.setStyleSheet("font-size: 14px; color: #dc3545;")

    def _auto_cancel_order(self):
        runner = get_service_runner()
        runner.run(
            self._cancel_order_in_thread,
            on_success=self._on_auto_cancel_success,
            on_error=lambda e: QMessageBox.critical(self, "错误", f"取消订单失败: {e}")
        )
    
    def _cancel_order_in_thread(self):
        stock_restore_errors = []
        orders = self._order_repo.find_by_order_id(self._order_id)
        for order in orders:
            try:
                self._inventory_repo.update_stock(order.product_id, order.quantity)
            except Exception as stock_error:
                stock_restore_errors.append(f"产品 {order.product_id}: {stock_error}")
            
            order.status = int(OrderStatus.CANCELLED)
            self._order_repo.update_order(order)
        
        return stock_restore_errors
    
    def _on_auto_cancel_success(self, stock_restore_errors):
        message = "支付时间已过，订单已自动取消"
        if stock_restore_errors:
            message += f"\n\n注意: 部分库存恢复失败:\n" + "\n".join(stock_restore_errors[:3])
        
        QMessageBox.warning(self, "支付超时", message)
        self.payment_cancelled.emit()
        self.back_to_main.emit()

    def _on_cancel_payment_clicked(self):
        reply = QMessageBox.question(
            self, "确认取消",
            "取消付款后，库存将保留30分钟。\n30分钟内未付款，订单将自动取消。\n确定要取消付款吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._countdown_timer:
                self._countdown_timer.stop()
            
            QMessageBox.information(
                self, "已取消付款",
                f"您已取消付款。\n库存将保留{self._remaining_seconds // 60}分钟。\n请在时间内完成支付。"
            )
            self.payment_cancelled.emit()
            self.back_to_main.emit()

    def _on_cancel_order_clicked(self):
        reply = QMessageBox.question(
            self, "确认取消订单",
            "确定要取消此订单吗？\n订单将被取消，库存将被恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            runner = get_service_runner()
            runner.run(
                self._cancel_order_in_thread,
                on_success=self._on_manual_cancel_success,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"取消订单失败: {e}")
            )
    
    def _on_manual_cancel_success(self, stock_restore_errors):
        if self._countdown_timer:
            self._countdown_timer.stop()
        
        message = "订单已取消，库存已恢复。"
        if stock_restore_errors:
            message += f"\n\n注意: 部分库存恢复失败:\n" + "\n".join(stock_restore_errors[:3])
        
        QMessageBox.information(self, "订单已取消", message)
        self.payment_cancelled.emit()
        self.back_to_main.emit()

    def _on_payment_completed_clicked(self):
        reply = QMessageBox.question(
            self, "确认支付",
            "请确认您已完成支付。\n确定要提交吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            runner = get_service_runner()
            runner.run(
                self._complete_payment_in_thread,
                on_success=self._on_payment_complete_success,
                on_error=lambda e: QMessageBox.critical(self, "错误", f"更新订单状态失败: {e}")
            )
    
    def _complete_payment_in_thread(self):
        orders = self._order_repo.find_by_order_id(self._order_id)
        for order in orders:
            order.status = int(OrderStatus.PENDING_SHIP)
            order.payment_time = datetime.now()
            self._order_repo.update_order(order)
        return True
    
    def _on_payment_complete_success(self, _):
        if self._countdown_timer:
            self._countdown_timer.stop()
        
        QMessageBox.information(
            self, "支付成功",
            f"订单 {self._order_id} 支付成功！\n请等待发货。"
        )
        self.payment_completed.emit()
        self.back_to_main.emit()

    def closeEvent(self, event):
        if self._countdown_timer:
            self._countdown_timer.stop()
        event.accept()
