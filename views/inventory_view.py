import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QDialog, QFormLayout, QSpinBox,
    QComboBox, QFileDialog, QProgressDialog, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
import uuid

from database import InventoryRepository
from models import Inventory
from enums import InventoryStatus
from services import ExcelService
from utils import get_service_runner


class InventoryQueryView(QWidget):
    back_to_main = pyqtSignal()
    def __init__(self):
        super().__init__()
        self._inventory_repo = InventoryRepository()
        self._setup_ui()
        self._load_inventory()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("库存查询")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        layout.addLayout(top_bar)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        search_layout = QHBoxLayout()
        self._search_entry = QLineEdit()
        self._search_entry.setPlaceholderText("搜索产品名称...")
        search_layout.addWidget(self._search_entry)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._on_search_clicked)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "产品类型", "产品名称", "品牌", "产品型号", "库存数量", "状态", "预计补货时间"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def _load_inventory(self):
        runner = get_service_runner()
        runner.run(
            self._inventory_repo.find_all_inventory,
            on_success=self._populate_table,
            on_error=lambda e: QMessageBox.critical(self, "错误", f"加载库存失败: {e}")
        )

    def _populate_table(self, inventory):
        self._table.setRowCount(0)
        
        for item in inventory:
            row = self._table.rowCount()
            self._table.insertRow(row)

            type_item = QTableWidgetItem(item.product_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, type_item)

            name_item = QTableWidgetItem(item.product_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, name_item)

            manufacturer_item = QTableWidgetItem(item.manufacturer)
            manufacturer_item.setFlags(manufacturer_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 2, manufacturer_item)

            model_item = QTableWidgetItem(item.product_model or "")
            model_item.setFlags(model_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 3, model_item)
            
            stock_item = QTableWidgetItem(str(item.stock_quantity))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 4, stock_item)
            
            status_item = QTableWidgetItem(str(InventoryStatus(item.status)))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 5, status_item)
            
            arrival_item = QTableWidgetItem(
                item.expected_arrival.strftime('%Y-%m-%d') if item.expected_arrival else "无")
            arrival_item.setFlags(arrival_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 6, arrival_item)
            


    def _on_search_clicked(self):
        keyword = self._search_entry.text().strip()
        
        def do_search():
            if keyword:
                return self._inventory_repo.search_inventory(keyword)
            else:
                return self._inventory_repo.find_all_inventory()
        
        runner = get_service_runner()
        runner.run(
            do_search,
            on_success=self._populate_table,
            on_error=lambda e: QMessageBox.critical(self, "错误", f"搜索失败: {e}")
        )


class InventoryManagementView(QWidget):
    back_to_main = pyqtSignal()
    def __init__(self):
        super().__init__()
        self._inventory_repo = InventoryRepository()
        self._excel_service = ExcelService()
        self._setup_ui()
        self._load_inventory()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top_bar = QHBoxLayout()

        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)

        top_bar.addStretch()

        title_label = QLabel("库存管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        import_btn = QPushButton("从Excel导入")
        import_btn.clicked.connect(self._on_import_clicked)
        top_bar.addWidget(import_btn)

        add_btn = QPushButton("+ 添加产品")
        add_btn.clicked.connect(self._on_add_clicked)
        top_bar.addWidget(add_btn)

        layout.addLayout(top_bar)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        self._table = QTableWidget()
        self._table.setColumnCount(10)
        self._table.setHorizontalHeaderLabels([
            "产品ID", "产品名称", "产品类型", "品牌", "产品型号", "库存数量", "已售数量", "状态", "预计补货时间", "操作"
        ])
        self._table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().sectionResized.connect(self._refresh_table_text)
        layout.addWidget(self._table)

    def _load_inventory(self):
        runner = get_service_runner()
        runner.run(
            self._inventory_repo.find_all_inventory,
            on_success=self._populate_table,
            on_error=lambda e: QMessageBox.critical(self, "错误", f"加载库存失败: {e}")
        )

    def _populate_table(self, inventory):
        self._table.setRowCount(0)

        for item in inventory:
            row = self._table.rowCount()
            self._table.insertRow(row)

            id_item = QTableWidgetItem(item.product_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(item.product_name)
            self._table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem(item.product_type)
            self._table.setItem(row, 2, type_item)

            manufacturer_item = QTableWidgetItem(item.manufacturer)
            self._table.setItem(row, 3, manufacturer_item)

            model_item = QTableWidgetItem(item.product_model or "")
            self._table.setItem(row, 4, model_item)

            stock_item = QTableWidgetItem(str(item.stock_quantity))
            self._table.setItem(row, 5, stock_item)

            sold_item = QTableWidgetItem(str(item.sold_quantity))
            self._table.setItem(row, 6, sold_item)

            status_item = QTableWidgetItem(str(InventoryStatus(item.status)))
            self._table.setItem(row, 7, status_item)

            arrival_item = QTableWidgetItem(
                item.expected_arrival.strftime('%Y-%m-%d') if item.expected_arrival else "无")
            self._table.setItem(row, 8, arrival_item)

            action_layout = QHBoxLayout()
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, pid=item.product_id: self._on_edit_clicked(pid))
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, pid=item.product_id: self._on_delete_clicked(pid))
            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)
            self._table.setCellWidget(row, 9, action_widget)

    def _on_edit_clicked(self, product_id: str):
        inventory = self._inventory_repo.find_inventory_by_id(product_id)
        if not inventory:
            QMessageBox.warning(self, "错误", "未找到该产品")
            return

        dialog = EditInventoryDialog(self, inventory[0])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            def do_update():
                self._inventory_repo.update_inventory(data)

            runner = get_service_runner()
            runner.run(
                do_update,
                on_success=lambda _: self._on_edit_success(),
                on_error=lambda e: QMessageBox.critical(self, "错误", f"编辑失败: {e}")
            )

    def _on_edit_success(self):
        self._load_inventory()
        QMessageBox.information(self, "成功", "产品已更新")

    def _refresh_table_text(self):
        self._table.resizeRowsToContents()

    def _on_add_clicked(self):
        dialog = AddInventoryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            inventory = Inventory(
                product_id=str(uuid.uuid4()),
                product_name=data['product_name'],
                product_type=data['product_type'],
                manufacturer=data['manufacturer'],
                product_model=data['product_model'],
                stock_quantity=data['stock_quantity'],
                status=int(InventoryStatus.NORMAL),
            )
            
            def do_add():
                self._inventory_repo.create_inventory(inventory)
            
            runner = get_service_runner()
            runner.run(
                do_add,
                on_success=lambda _: self._on_add_success(),
                on_error=lambda e: QMessageBox.critical(self, "错误", f"添加失败: {e}")
            )
    
    def _on_add_success(self):
        self._load_inventory()
        QMessageBox.information(self, "成功", "产品已添加")

    def _on_delete_clicked(self, product_id: str):
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除此产品吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            def do_delete():
                self._inventory_repo.delete_inventory(product_id)
            
            runner = get_service_runner()
            runner.run(
                do_delete,
                on_success=lambda _: self._on_delete_success(),
                on_error=lambda e: QMessageBox.critical(self, "错误", f"删除失败: {e}")
            )
    
    def _on_delete_success(self):
        self._load_inventory()
        QMessageBox.information(self, "成功", "产品已删除")

    def _on_import_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return

        self._progress_dialog = QProgressDialog(
            "正在导入库存数据...", None, 0, 0, self
        )
        self._progress_dialog.setWindowTitle("导入中")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setCancelButton(None)
        self._progress_dialog.show()

        runner = get_service_runner()
        runner.run(
            self._excel_service.import_inventory_from_excel,
            args=(file_path,),
            on_success=self._on_inventory_import_success,
            on_error=self._on_inventory_import_error,
            on_finished=self._on_inventory_import_finished
        )
    
    def _on_inventory_import_success(self, result):
        success_count, errors = result
        
        message = f"导入完成！\n成功导入: {success_count} 条记录"
        
        if errors:
            message += f"\n\n⚠ 有 {len(errors)} 个错误:"
            for error in errors[:5]:
                message += f"\n• {error}"
            if len(errors) > 5:
                message += f"\n...还有 {len(errors) - 5} 个错误"
        
        if success_count > 0:
            QMessageBox.information(self, "导入结果", message)
            self._load_inventory()
        else:
            QMessageBox.warning(self, "导入结果", message)
    
    def _on_inventory_import_error(self, error: Exception):
        QMessageBox.critical(self, "导入失败", f"导入库存失败: {error}")
    
    def _on_inventory_import_finished(self):
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None


class AddInventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加产品")
        self.setMinimumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        
        self._product_name_entry = QLineEdit()
        layout.addRow("产品名称:", self._product_name_entry)
        
        self._product_type_entry = QLineEdit()
        layout.addRow("产品类型:", self._product_type_entry)
        
        self._manufacturer_entry = QLineEdit()
        layout.addRow("厂家:", self._manufacturer_entry)
        
        self._product_model_entry = QLineEdit()
        layout.addRow("型号:", self._product_model_entry)
        
        self._stock_quantity_spin = QSpinBox()
        self._stock_quantity_spin.setRange(0, 999999)
        layout.addRow("库存数量:", self._stock_quantity_spin)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self) -> dict:
        return {
            'product_name': self._product_name_entry.text().strip(),
            'product_type': self._product_type_entry.text().strip(),
            'manufacturer': self._manufacturer_entry.text().strip(),
            'product_model': self._product_model_entry.text().strip(),
            'stock_quantity': self._stock_quantity_spin.value(),
        }

class EditInventoryDialog(QDialog):
    def __init__(self, parent, inventory):
        super().__init__(parent)
        self.setWindowTitle("编辑库存")
        self.setMinimumWidth(300)
        self._inventory = inventory
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        self._product_name_entry = QLineEdit(self._inventory.product_name)
        layout.addRow("产品名称:", self._product_name_entry)

        self._product_type_entry = QLineEdit(self._inventory.product_type)
        layout.addRow("产品类型:", self._product_type_entry)

        self._manufacturer_entry = QLineEdit(self._inventory.manufacturer)
        layout.addRow("品牌:", self._manufacturer_entry)

        self._product_model_entry = QLineEdit(self._inventory.product_model or "")
        layout.addRow("型号:", self._product_model_entry)

        self._stock_quantity_spin = QSpinBox()
        self._stock_quantity_spin.setRange(0, 999999)
        self._stock_quantity_spin.setValue(self._inventory.stock_quantity)
        layout.addRow("库存数量:", self._stock_quantity_spin)

        self._sold_quantity_spin = QSpinBox()
        self._sold_quantity_spin.setRange(0, 999999)
        self._sold_quantity_spin.setValue(self._inventory.sold_quantity)
        layout.addRow("已售数量:", self._sold_quantity_spin)

        self._status_combo = QComboBox()
        self._status_combo.addItems([str(status) for status in InventoryStatus])
        self._status_combo.setCurrentText(str(InventoryStatus(self._inventory.status)))
        self._status_combo.currentTextChanged.connect(self._on_status_changed)
        layout.addRow("状态:", self._status_combo)

        self._expected_arrival_date = QDateEdit()
        self._expected_arrival_date.setCalendarPopup(True)
        if self._inventory.status == InventoryStatus.NORMAL:
            self._expected_arrival_date.setEnabled(True)
        else:
            self._expected_arrival_date.setDisabled(True)
        if self._inventory.expected_arrival:
            self._expected_arrival_date.setDate(self._inventory.expected_arrival.date())
        else:
            self._expected_arrival_date.setDate(datetime.datetime.now().date())
        layout.addRow("预计补货时间:", self._expected_arrival_date)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _on_status_changed(self, status_text: str):
        if status_text == "正常":
            self._expected_arrival_date.setEnabled(True)
        else:
            self._expected_arrival_date.setDisabled(True)

    def get_data(self) -> Inventory:
        return Inventory(
            product_id=self._inventory.product_id,
            product_name=self._product_name_entry.text().strip(),
            product_type=self._product_type_entry.text().strip(),
            manufacturer=self._manufacturer_entry.text().strip(),
            product_model=self._product_model_entry.text().strip(),
            stock_quantity=self._stock_quantity_spin.value(),
            sold_quantity=self._sold_quantity_spin.value(),
            status=InventoryStatus.from_string(self._status_combo.currentText()).value,
            expected_arrival=self._expected_arrival_date.date().toPyDate(),
        )