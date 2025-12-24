from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
import uuid

from services import UserService
from models import User
from enums import UserRole


class UserManagementView(QWidget):
    back_to_main = pyqtSignal()

    def __init__(self, user_service: UserService):
        super().__init__()
        self._user_service = user_service
        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("👥 用户管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        add_user_btn = QPushButton("+ 添加用户")
        add_user_btn.clicked.connect(self._on_add_user_clicked)
        top_bar.addWidget(add_user_btn)
        
        layout.addLayout(top_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "用户ID", "用户名", "显示名称", "角色", "部门", "状态", "操作"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def _load_users(self):
        try:
            users = self._user_service.get_all_users()
            self._populate_table(users)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载用户失败: {e}")

    def _populate_table(self, users):
        self._table.setRowCount(0)
        
        for user in users:
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            self._table.setItem(row, 0, QTableWidgetItem(user.user_id[:8] + "..."))
            self._table.setItem(row, 1, QTableWidgetItem(user.username))
            self._table.setItem(row, 2, QTableWidgetItem(user.display_name))
            self._table.setItem(row, 3, QTableWidgetItem(str(UserRole(user.role))))
            self._table.setItem(row, 4, QTableWidgetItem(user.department or ""))
            self._table.setItem(row, 5, QTableWidgetItem("活跃" if user.is_active else "禁用"))
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, uid=user.user_id: self._on_delete_user(uid))
            self._table.setCellWidget(row, 6, delete_btn)

    def _on_add_user_clicked(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_user_data()
            try:
                user = User(
                    user_id=str(uuid.uuid4()),
                    username=user_data['username'],
                    display_name=user_data['display_name'],
                    role=int(user_data['role']),
                    department=user_data['department'],
                    is_active=True,
                )
                user.set_password(user_data['password'])
                
                self._user_service.create_user(user)
                self._load_users()
                QMessageBox.information(self, "成功", "用户创建成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建用户失败: {e}")

    def _on_delete_user(self, user_id: str):
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除此用户吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._user_service.delete_user(user_id)
                self._load_users()
                QMessageBox.information(self, "成功", "用户已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除用户失败: {e}")


class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加用户")
        self.setMinimumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        
        self._username_entry = QLineEdit()
        layout.addRow("用户名:", self._username_entry)
        
        self._password_entry = QLineEdit()
        self._password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("密码:", self._password_entry)
        
        self._display_name_entry = QLineEdit()
        layout.addRow("显示名称:", self._display_name_entry)
        
        self._role_combo = QComboBox()
        for role in UserRole:
            self._role_combo.addItem(str(role), role)
        layout.addRow("角色:", self._role_combo)
        
        self._department_entry = QLineEdit()
        layout.addRow("部门:", self._department_entry)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_user_data(self) -> dict:
        return {
            'username': self._username_entry.text().strip(),
            'password': self._password_entry.text(),
            'display_name': self._display_name_entry.text().strip(),
            'role': self._role_combo.currentData(),
            'department': self._department_entry.text().strip(),
        }
