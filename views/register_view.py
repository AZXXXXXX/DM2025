

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from models import User
from enums import UserRole
from utils import get_service_runner


class RegisterView(QWidget):
    
    
    registration_success = pyqtSignal()                                      
    back_to_login = pyqtSignal()                                               

    def __init__(self, user_service):
        
        super().__init__()
        self._user_service = user_service
        self._setup_ui()

    def _setup_ui(self):
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(15)
        
               
        title_label = QLabel("客户注册")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
                   
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        layout.addStretch()
        
                     
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
                  
        self._username_entry = QLineEdit()
        self._username_entry.setPlaceholderText("请输入用户名 (至少3个字符)")
        form_layout.addRow("用户名:", self._username_entry)
        
                  
        self._password_entry = QLineEdit()
        self._password_entry.setPlaceholderText("请输入密码")
        self._password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("密码:", self._password_entry)
        
                          
        self._confirm_password_entry = QLineEdit()
        self._confirm_password_entry.setPlaceholderText("请确认密码")
        self._confirm_password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("确认密码:", self._confirm_password_entry)
        
                      
        self._display_name_entry = QLineEdit()
        self._display_name_entry.setPlaceholderText("请输入显示名称")
        form_layout.addRow("显示名称:", self._display_name_entry)
        
               
        self._email_entry = QLineEdit()
        self._email_entry.setPlaceholderText("请输入邮箱")
        form_layout.addRow("邮箱:", self._email_entry)
        
               
        self._phone_entry = QLineEdit()
        self._phone_entry.setPlaceholderText("请输入手机号")
        form_layout.addRow("手机号:", self._phone_entry)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
                     
        self._error_label = QLabel("")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet("color: red;")
        layout.addWidget(self._error_label)
        
                 
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
                         
        self._register_button = QPushButton("注册")
        self._register_button.setFixedHeight(40)
        self._register_button.clicked.connect(self._on_register_clicked)
        button_layout.addWidget(self._register_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
                              
        back_button = QPushButton("返回登录")
        back_button.clicked.connect(self.back_to_login.emit)
        button_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()

    def _on_register_clicked(self):
        
        username = self._username_entry.text().strip()
        password = self._password_entry.text()
        confirm_password = self._confirm_password_entry.text()
        display_name = self._display_name_entry.text().strip()
        email = self._email_entry.text().strip()
        phone = self._phone_entry.text().strip()
        
                    
        if not username or not password:
            self._error_label.setText("用户名和密码不能为空")
            return
        
        if len(username) < 3:
            self._error_label.setText("用户名至少需要3个字符")
            return
        
        if password != confirm_password:
            self._error_label.setText("两次密码输入不一致")
            return
        
                                
        if email and '@' not in email:
            self._error_label.setText("请输入有效的邮箱地址")
            return
        
                                                                               
        if phone and not all(c.isdigit() or c in '+-() ' for c in phone):
            self._error_label.setText("请输入有效的手机号")
            return
        
        self._register_button.setEnabled(False)
        self._error_label.setText("")
        
                            
        user = User(
            username=username,
            display_name=display_name if display_name else username,
            role=int(UserRole.CUSTOMER),
            email=email,
            phone=phone,
            is_active=True,
        )
        user.set_password(password)
        
                                               
        runner = get_service_runner()
        runner.run(
            self._user_service.register_customer,
            args=(user,),
            on_success=self._on_register_success,
            on_error=self._on_register_error,
            on_finished=lambda: self._register_button.setEnabled(True)
        )
    
    def _on_register_success(self, _):
        
        QMessageBox.information(
            self, "注册成功", "您的账号已创建，请登录"
        )
        self._clear_form()
        self.registration_success.emit()
    
    def _on_register_error(self, error: Exception):
        
                                                                   
        self._error_label.setText("注册失败，用户名可能已被使用")

    def _clear_form(self):
        
        self._username_entry.clear()
        self._password_entry.clear()
        self._confirm_password_entry.clear()
        self._display_name_entry.clear()
        self._email_entry.clear()
        self._phone_entry.clear()
        self._error_label.setText("")
