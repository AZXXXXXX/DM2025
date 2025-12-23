

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils import get_service_runner


class LoginView(QWidget):
    
    
    login_success = pyqtSignal(object)                                
    navigate_to_register = pyqtSignal()                                     

    def __init__(self, user_service):
        
        super().__init__()
        self._user_service = user_service
        self._setup_ui()

    def _setup_ui(self):
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)
        
               
        title_label = QLabel("丝芙兰A店商品内部管理系统")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
                  
        subtitle_label = QLabel("请登录以继续")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(subtitle_label)
        
                   
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        layout.addStretch()
        
                     
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
                  
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(60)
        self._username_entry = QLineEdit()
        self._username_entry.setPlaceholderText("请输入用户名")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self._username_entry)
        form_layout.addLayout(username_layout)
        
                  
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(60)
        self._password_entry = QLineEdit()
        self._password_entry.setPlaceholderText("请输入密码")
        self._password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_entry.returnPressed.connect(self._on_login_clicked)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self._password_entry)
        form_layout.addLayout(password_layout)
        
        layout.addWidget(form_widget)
        
        layout.addStretch()
        
                     
        self._error_label = QLabel("")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet("color: red;")
        layout.addWidget(self._error_label)
        
                      
        self._login_button = QPushButton("登录")
        self._login_button.setFixedHeight(40)
        self._login_button.clicked.connect(self._on_login_clicked)
        layout.addWidget(self._login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
                         
        register_button = QPushButton("客户注册")
        register_button.clicked.connect(self.navigate_to_register.emit)
                                                                                  
        
        layout.addStretch()
        
                                  
                                    
        hint_label = QLabel("默认用户: admin / admin123")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(hint_label)

    def _on_login_clicked(self):
        
        username = self._username_entry.text().strip()
        password = self._password_entry.text()
        
        if not username or not password:
            self._error_label.setText("请输入用户名和密码")
            return
        
        self._login_button.setEnabled(False)
        self._error_label.setText("")
        
                                        
        runner = get_service_runner()
        runner.run(
            self._user_service.login,
            args=(username, password),
            on_success=self._on_login_success,
            on_error=self._on_login_error,
            on_finished=lambda: self._login_button.setEnabled(True)
        )
    
    def _on_login_success(self, user):
        
        QMessageBox.information(
            self, "登录成功", f"欢迎, {user.display_name}!"
        )
        self.login_success.emit(user)
    
    def _on_login_error(self, error: Exception):
        
        self._error_label.setText(f"登录失败: {error}")
