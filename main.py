import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt

from database import get_db, InventoryRepository
from services import (
    UserService, OrderService, CustomerService,
    StatisticsService, ExcelService
)
from views import (
    LoginView, RegisterView, MainView, DashboardView, DataFilterView,
    UserManagementView, PlaceOrderView,
    InventoryQueryView, InventoryManagementView, PaymentView,
    ReturnRequestView, OrderStatusManagementView
)
from utils import get_service_runner


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("丝芙兰A店商品内部管理系统")
        self.setMinimumSize(800, 600)
        
                             
        self._init_database()
        
                             
        self._init_services()
        
                                              
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        
                      
        self._create_views()
        
                         
        self._show_login()

    def _init_database(self):
        db_path = os.environ.get('DATABASE_PATH', 'mysql+pymysql://root:xiamingxing0526@localhost/order_system')
        db = get_db()
        db.connect(db_path)

    def _init_services(self):
        self._user_service = UserService()
        self._order_service = OrderService()
        self._customer_service = CustomerService()
        self._statistics_service = StatisticsService()
        self._excel_service = ExcelService()
        
                              
        self._order_service.set_user_service(self._user_service)
        self._statistics_service.set_user_service(self._user_service)
        
                                  
        self._inventory_repo = InventoryRepository()
        self._statistics_service.set_inventory_repo(self._inventory_repo)

    def _create_views(self):
        self._login_view = LoginView(self._user_service)
        self._login_view.login_success.connect(self._on_login_success)
        self._login_view.navigate_to_register.connect(self._show_register)
        self._stack.addWidget(self._login_view)

    def _show_login(self):
        self.resize(400, 350)
        self._stack.setCurrentWidget(self._login_view)

    def _show_register(self):
        self.resize(400, 500)
        
        register_view = RegisterView(self._user_service)
        register_view.registration_success.connect(self._show_login)
        register_view.back_to_login.connect(self._show_login)
        
        self._stack.addWidget(register_view)
        self._stack.setCurrentWidget(register_view)

    def _on_login_success(self, user):
        self._show_main_view()

    def _show_main_view(self):
        self.resize(900, 600)
        
        main_view = MainView(self._user_service, self._excel_service)
        main_view.logout_requested.connect(self._on_logout)
        main_view.navigate_to_dashboard.connect(self._show_dashboard)
        main_view.navigate_to_data_filter.connect(self._show_data_filter)
        main_view.navigate_to_user_management.connect(self._show_user_management)
        main_view.navigate_to_inventory_query.connect(self._show_inventory_query)
        main_view.navigate_to_inventory_management.connect(self._show_inventory_management)
        main_view.navigate_to_place_order.connect(self._show_place_order)
        main_view.navigate_to_return_request.connect(self._show_return_request)
        main_view.navigate_to_order_status_management.connect(self._show_order_status_management)
        main_view.file_upload_requested.connect(self._on_file_upload)
        
        self._stack.addWidget(main_view)
        self._stack.setCurrentWidget(main_view)

    def _on_logout(self):
        self._user_service.logout()
        self._show_login()

    def _show_dashboard(self):
        self.resize(1000, 700)
        
        dashboard = DashboardView(self._statistics_service)
        dashboard.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(dashboard)
        self._stack.setCurrentWidget(dashboard)

    def _show_data_filter(self):
        self.resize(1200, 800)
        
        data_filter = DataFilterView(self._order_service)
        data_filter.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(data_filter)
        self._stack.setCurrentWidget(data_filter)

    def _show_user_management(self):
        self.resize(1000, 700)
        
        user_mgmt = UserManagementView(self._user_service)
        user_mgmt.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(user_mgmt)
        self._stack.setCurrentWidget(user_mgmt)

    def _show_inventory_query(self):
        self.resize(900, 600)
        
        inventory_query = InventoryQueryView()
        inventory_query.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(inventory_query)
        self._stack.setCurrentWidget(inventory_query)

    def _show_inventory_management(self):
        self.resize(1000, 700)
        
        inventory_mgmt = InventoryManagementView()
        inventory_mgmt.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(inventory_mgmt)
        self._stack.setCurrentWidget(inventory_mgmt)

    def _show_place_order(self):
        self.resize(900, 600)
        
        place_order = PlaceOrderView(
            self._order_service,
            user_service=self._user_service,
            inventory_repo=self._inventory_repo,
            show_payment_callback=self._show_payment
        )
        place_order.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(place_order)
        self._stack.setCurrentWidget(place_order)

    def _show_payment(self, order_id: str, total_products: int, order_time):
        self.resize(600, 700)
        
        from datetime import datetime
        if not isinstance(order_time, datetime):
            order_time = datetime.now()
        
        payment_view = PaymentView(
            order_id=order_id,
            total_products=total_products,
            order_time=order_time,
            order_service=self._order_service,
            inventory_repo=self._inventory_repo
        )
        payment_view.back_to_main.connect(self._show_main_view)
        payment_view.payment_completed.connect(self._show_main_view)
        payment_view.payment_cancelled.connect(self._show_main_view)
        
        self._stack.addWidget(payment_view)
        self._stack.setCurrentWidget(payment_view)

    def _show_return_request(self):
        self.resize(1000, 700)
        
        return_request = ReturnRequestView(
            self._order_service,
            user_service=self._user_service
        )
        return_request.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(return_request)
        self._stack.setCurrentWidget(return_request)

    def _show_order_status_management(self):
        self.resize(1200, 800)
        
        order_status_mgmt = OrderStatusManagementView(
            self._order_service,
            user_service=self._user_service
        )
        order_status_mgmt.back_to_main.connect(self._show_main_view)
        
        self._stack.addWidget(order_status_mgmt)
        self._stack.setCurrentWidget(order_status_mgmt)

    def _on_file_upload(self, file_path: str):
                              
        self._progress_dialog = QProgressDialog(
            "正在导入数据...", None, 0, 0, self
        )
        self._progress_dialog.setWindowTitle("导入中")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setCancelButton(None)
        self._progress_dialog.show()
        
                                         
        runner = get_service_runner()
        runner.run(
            self._excel_service.import_excel_with_customers_and_users,
            args=(file_path,),
            on_success=self._on_import_success,
            on_error=self._on_import_error,
            on_finished=self._on_import_finished
        )
    
    def _on_import_success(self, result):
        message = (
            f"导入完成！\n\n"
            f"✓ 创建订单: {result.orders_created} 条\n"
            f"✓ 创建客户: {result.customers_created} 个\n"
            f"✓ 创建账号: {result.users_created} 个"
        )
        
        if result.errors:
            message += f"\n\n⚠ 有 {len(result.errors)} 个错误"
            for error in result.errors[:5]:                       
                print(f"[Import Error] {error}")
        
        if result.created_accounts:
            try:
                account_file = ExcelService.export_created_accounts_to_excel(
                    result.created_accounts
                )
                message += f"\n\n📄 账号密码已导出至:\n{account_file}"
            except Exception as e:
                message += f"\n\n⚠ 导出账号信息失败: {e}"
        
        QMessageBox.information(self, "导入结果", message)
    
    def _on_import_error(self, error: Exception):
        QMessageBox.critical(self, "导入失败", f"导入数据失败: {error}")
    
    def _on_import_finished(self):
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

    def closeEvent(self, event):
        db = get_db()
        db.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("丝芙兰A店商品内部管理系统")
    app.setApplicationVersion("1.0.0")
    
               
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
