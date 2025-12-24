from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from enums import UserRole


class MainView(QWidget):
    logout_requested = pyqtSignal()
    navigate_to_dashboard = pyqtSignal()
    navigate_to_data_filter = pyqtSignal()
    navigate_to_user_management = pyqtSignal()
    navigate_to_inventory_query = pyqtSignal()
    navigate_to_inventory_management = pyqtSignal()
    navigate_to_place_order = pyqtSignal()
    navigate_to_return_request = pyqtSignal()
    navigate_to_order_status_management = pyqtSignal()
    file_upload_requested = pyqtSignal(str)

    def __init__(self, user_service, excel_service=None):
        super().__init__()
        self._user_service = user_service
        self._excel_service = excel_service
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        top_bar = self._create_top_bar()
        layout.addLayout(top_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        center_layout = self._create_center_content()
        layout.addLayout(center_layout)
        
        layout.addStretch()
        
        copyright_label = QLabel("© 2025 丝芙兰A店商品内部管理系统")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: gray;")
        layout.addWidget(copyright_label)

    def _create_top_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        
        if self._user_service.is_logged_in():
            user = self._user_service.get_current_user()
            role_str = str(UserRole(user.role))
            user_label = QLabel(f"欢迎, {user.display_name} ({role_str})")
        else:
            user_label = QLabel("未登录")
        layout.addWidget(user_label)
        
        logout_btn = QPushButton("退出登录")
        logout_btn.clicked.connect(self._on_logout_clicked)
        layout.addWidget(logout_btn)
        
        layout.addStretch()
        
        can_manage_users = self._user_service.can_manage_users()
        
        if can_manage_users:
            user_mgmt_btn = QPushButton("用户管理")
            user_mgmt_btn.clicked.connect(self.navigate_to_user_management.emit)
            layout.addWidget(user_mgmt_btn)
        
        return layout

    def _create_center_content(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        can_upload = self._user_service.can_create()
        can_manage_settings = self._user_service.can_view_settings()
        current_user = self._user_service.get_current_user()
        is_customer = current_user and current_user.role == UserRole.CUSTOMER
        
        if can_upload:
            upload_btn = QPushButton("📤 上传数据")
            upload_btn.setFixedHeight(50)
            upload_btn.clicked.connect(self._on_upload_clicked)
            layout.addWidget(upload_btn)
        
        filter_btn = QPushButton("🔍 筛选订单数据")
        filter_btn.setFixedHeight(50)
        filter_btn.clicked.connect(self.navigate_to_data_filter.emit)
        layout.addWidget(filter_btn)
        
        if not is_customer:
            dashboard_btn = QPushButton("📊 数据统计")
            dashboard_btn.setFixedHeight(50)
            dashboard_btn.clicked.connect(self.navigate_to_dashboard.emit)
            layout.addWidget(dashboard_btn)
        
        inventory_query_btn = QPushButton("📦 库存查询")
        inventory_query_btn.setFixedHeight(50)
        inventory_query_btn.clicked.connect(self.navigate_to_inventory_query.emit)
        layout.addWidget(inventory_query_btn)
        
        place_order_btn = QPushButton("🛒 下单")
        place_order_btn.setFixedHeight(50)
        place_order_btn.clicked.connect(self.navigate_to_place_order.emit)
        layout.addWidget(place_order_btn)
        
        return_request_btn = QPushButton("📦 退货申请")
        return_request_btn.setFixedHeight(50)
        return_request_btn.clicked.connect(self.navigate_to_return_request.emit)
        layout.addWidget(return_request_btn)
        
        if can_manage_settings:
            inventory_mgmt_btn = QPushButton("📋 库存管理")
            inventory_mgmt_btn.setFixedHeight(50)
            inventory_mgmt_btn.clicked.connect(self.navigate_to_inventory_management.emit)
            layout.addWidget(inventory_mgmt_btn)
        
        if can_upload:
            order_status_btn = QPushButton("📝 订单状态管理")
            order_status_btn.setFixedHeight(50)
            order_status_btn.clicked.connect(self.navigate_to_order_status_management.emit)
            layout.addWidget(order_status_btn)
        
        return layout

    def _on_logout_clicked(self):
        self._user_service.logout()
        self.logout_requested.emit()

    def _on_upload_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            self.file_upload_requested.emit(file_path)
