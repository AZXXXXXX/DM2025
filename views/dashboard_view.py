from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from services import StatisticsService
from utils import get_service_runner


CHART_COLORS = [
    "#4CAF50",         
    "#2196F3",        
    "#FF9800",          
    "#9C27B0",          
    "#F44336",       
    "#00BCD4",        
    "#FFEB3B",          
    "#795548",         
]


class DashboardView(QWidget):
    back_to_main = pyqtSignal()

    def __init__(self, statistics_service: StatisticsService):
        super().__init__()
        self._statistics_service = statistics_service
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
                 
        top_bar = QHBoxLayout()
        
        back_btn = QPushButton("← 返回首页")
        back_btn.clicked.connect(self.back_to_main.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        title_label = QLabel("📊 数据统计仪表板")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()

        layout.addLayout(top_bar)
        
                   
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
                                 
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setSpacing(20)
        
        scroll.setWidget(self._content_widget)
        layout.addWidget(scroll)

    def _load_data(self):
                                
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        loading_label = QLabel("加载中...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(loading_label)
        
                                               
        runner = get_service_runner()
        runner.run(
            self._fetch_all_stats,
            on_success=self._on_stats_loaded,
            on_error=self._on_stats_error
        )
    
    def _fetch_all_stats(self):
        
        return {
            'dash_stats': self._statistics_service.get_dashboard_stats(),
            'status_stats': self._statistics_service.get_order_status_distribution(),
            'customer_type_stats': self._statistics_service.get_order_customer_type_distribution(),
            'deadline_stats': self._statistics_service.get_deadline_distribution(),
            'inventory_stats': self._statistics_service.get_inventory_sales_stats(),
            'platform_stats': self._statistics_service.get_best_selling_platform(),
        }
    
    def _on_stats_loaded(self, stats):
        
                             
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        dash_stats = stats['dash_stats']
        status_stats = stats['status_stats']
        customer_type_stats = stats['customer_type_stats']
        deadline_stats = stats['deadline_stats']
        inventory_stats = stats['inventory_stats']
        
                           
        overview_card = self._create_overview_card(dash_stats)
        self._content_layout.addWidget(overview_card)
        
                                      
        status_card = self._create_distribution_card(
            "📈 订单状态分布",
            [(str(s.status), s.count) for s in status_stats]
            )
        self._content_layout.addWidget(status_card)
        
                                             
        customer_card = self._create_distribution_card(
            "🏪 客户类型分布",
            [(str(s.customer_type), s.count) for s in customer_type_stats]
            )
        self._content_layout.addWidget(customer_card)
        
                                     
        if inventory_stats:
            inventory_card = self._create_distribution_card(
                "📦 库存销售分析",
                [(f"{s.product_type}: 已售{s.total_sold}/余量{s.total_stock}", s.total_sold)
                 for s in inventory_stats]
            )
            self._content_layout.addWidget(inventory_card)
        
                                        
        if deadline_stats:
            deadline_card = self._create_distribution_card(
                "⏰ 发货截止日期分布",
                list(deadline_stats.items())
            )
            self._content_layout.addWidget(deadline_card)
        
        self._content_layout.addStretch()

    def _on_stats_error(self, error: Exception):
        
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error_label = QLabel(f"加载数据失败: {error}")
        error_label.setStyleSheet("color: red;")
        self._content_layout.addWidget(error_label)

    def _create_overview_card(self, stats) -> QWidget:
        
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        
        layout = QVBoxLayout(card)
        
        title = QLabel("📊 总览")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
                    
        grid = QGridLayout()
        grid.setSpacing(10)
        
        stats_data = [
            ("订单总数", str(stats.total_orders), "#4CAF50"),
            ("客户总数", str(stats.total_customers), "#2196F3"),
            ("用户总数", str(stats.total_users), "#9C27B0"),
            ("待处理订单", str(stats.pending_orders), "#FF9800"),
            ("已完成订单", str(stats.completed_orders), "#4CAF50"),
            ("临近截止", str(stats.near_deadline_orders), "#F44336"),
        ]
        
        for i, (label_text, value, color) in enumerate(stats_data):
            cell = QVBoxLayout()
            
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell.addWidget(label)
            
            value_label = QLabel(value)
            value_font = QFont()
            value_font.setPointSize(18)
            value_font.setBold(True)
            value_label.setFont(value_font)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setStyleSheet(f"color: {color};")
            cell.addWidget(value_label)
            
            cell_widget = QWidget()
            cell_widget.setLayout(cell)
            grid.addWidget(cell_widget, 0, i)
        
        layout.addLayout(grid)
        return card

    def _create_distribution_card(
        self, title: str, data: list
    ) -> QWidget:
        
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        if not data:
            empty_label = QLabel("暂无数据")
            layout.addWidget(empty_label)
            return card
        
                              
        max_count = max(item[1] for item in data) if data else 1
        if max_count == 0:
            max_count = 1

        for i, (label, count) in enumerate(data):
            row = QHBoxLayout()

            label_widget = QLabel(f"{label}: {count}")
            label_widget.setMinimumWidth(150)
            row.addWidget(label_widget)

                               
            bar_width = int((count / max_count) * 300)
            if bar_width < 20:
                bar_width = 20

            bar = QFrame()
            bar.setFixedSize(bar_width, 25)
            bar.setStyleSheet(f"background-color: {CHART_COLORS[i % len(CHART_COLORS)]};")
            row.addWidget(bar)

            row.addStretch()
            layout.addLayout(row)
        
        return card
