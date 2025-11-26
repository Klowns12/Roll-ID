from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QBrush, QColor
from datetime import datetime, timedelta

class DashboardTab(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
        
        # Initial data load
        self.refresh_data()
        
        # Set up auto-refresh timer (every 5 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # 5 seconds
        
        # Connect to storage signals if available
        if hasattr(storage, 'data_changed'):
            storage.data_changed.connect(self.refresh_data)
    
    def setup_ui(self):
        """Set up the dashboard UI components"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Dashboard Overview")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        # Total Rolls card
        self.total_master_data_card = self.create_stat_card("Total Master Data", "0", "#95db34")
        stats_layout.addWidget(self.total_master_data_card)

        # Total Rolls card
        self.total_rolls_card = self.create_stat_card("Total Rolls", "0", "#3498db")
        stats_layout.addWidget(self.total_rolls_card)
        
        # Active Rolls card
        self.active_rolls_card = self.create_stat_card("Active Rolls", "0", "#2ecc71")
        stats_layout.addWidget(self.active_rolls_card)
        
        # Low Stock card
        # self.low_stock_card = self.create_stat_card("Low Stock", "0", "#e74c3c")
        # stats_layout.addWidget(self.low_stock_card)
        
        # Recent Activities card
        self.recent_activities_card = self.create_stat_card("Today's Activities", "0", "#9b59b6")
        stats_layout.addWidget(self.recent_activities_card)
        
        layout.addLayout(stats_layout)
        
        # Recent Rolls table
        recent_rolls_group = QGroupBox("Recently Added Rolls")
        recent_rolls_layout = QVBoxLayout()
        
        self.recent_rolls_table = QTableWidget()
        self.recent_rolls_table.setColumnCount(5)
        self.recent_rolls_table.setHorizontalHeaderLabels(["Roll ID", "SKU", "Lot", "Width", "Location"])
        self.recent_rolls_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recent_rolls_table.verticalHeader().setVisible(False)
        self.recent_rolls_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_rolls_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        recent_rolls_layout.addWidget(self.recent_rolls_table)
        recent_rolls_group.setLayout(recent_rolls_layout)
        
        # Recent Activities table
        activities_group = QGroupBox("Recent Activities")
        activities_layout = QVBoxLayout()
        
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(4)
        self.activities_table.setHorizontalHeaderLabels(["Time", "Action", "Roll ID", "Details"])
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.activities_table.verticalHeader().setVisible(False)
        self.activities_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        activities_layout.addWidget(self.activities_table)
        activities_group.setLayout(activities_layout)
        
        # Add tables to main layout
        tables_layout = QHBoxLayout()
        tables_layout.addWidget(recent_rolls_group, 2)  # 2/3 width
        tables_layout.addWidget(activities_group, 1)    # 1/3 width
        
        layout.addLayout(tables_layout)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
    
    def create_stat_card(self, title, value, color):
        """Create a statistic card widget"""
        card = QGroupBox(title)
        card_layout = QVBoxLayout()
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        card.setLayout(card_layout)
        
        # Add some styling
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 10px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        
        return card
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        # Update stats cards
        self.update_stats_cards()
        
        # Update recent rolls table
        self.update_recent_rolls()
        
        # Update activities table
        self.update_recent_activities()
    
    def update_stats_cards(self):
        """Update the statistics cards with current data"""
        try:
            # Update master data count
            master_count = self.storage.get_master_data_count()
            self.total_master_data_card.findChild(QLabel).setText(str(master_count))
            
            # Update total rolls count
            total_rolls = self.storage.get_roll_count()
            self.total_rolls_card.findChild(QLabel).setText(str(total_rolls))
            
            # Update active rolls count
            active_rolls = self.storage.get_roll_active_count()
            self.active_rolls_card.findChild(QLabel).setText(str(active_rolls))
            
            # Update today's activities
            today = datetime.now().date()
            today_activities = len([
                log for log in self.storage.get_logs() 
                if datetime.fromisoformat(log.timestamp).date() == today
            ])
            self.recent_activities_card.findChild(QLabel).setText(str(today_activities))
            
        except Exception as e:
            print(f"Error updating stats cards: {e}")
    
    def update_recent_rolls(self):
        """Update the recent rolls table"""
        # Get recent rolls (last 10)
        all_rolls = self.storage.search_rolls()
        recent_rolls = sorted(
            all_rolls,
            key=lambda x: x.date_received,
            reverse=True
        )[:10]
        
        # Clear table
        self.recent_rolls_table.setRowCount(0)
        
        # Add rows
        for roll in recent_rolls:
            row = self.recent_rolls_table.rowCount()
            self.recent_rolls_table.insertRow(row)
            
            # Add items to the row
            self.recent_rolls_table.setItem(row, 0, QTableWidgetItem(roll.roll_id))
            self.recent_rolls_table.setItem(row, 1, QTableWidgetItem(roll.sku))
            self.recent_rolls_table.setItem(row, 2, QTableWidgetItem(roll.lot))
            self.recent_rolls_table.setItem(row, 3, QTableWidgetItem(roll.width or ""))
            self.recent_rolls_table.setItem(row, 4, QTableWidgetItem(roll.location))
            
            # Color code based on status
            if roll.status == 'used':
                for col in range(self.recent_rolls_table.columnCount()):
                    item = self.recent_rolls_table.item(row, col)
                    item.setBackground(QBrush(QColor(255, 200, 200)))  # Light red for used rolls
    
    def update_recent_activities(self):
        """Update the recent activities table"""
        # Get recent logs (last 10)
        logs = self.storage.get_logs(limit=10)
        
        # Clear table
        self.activities_table.setRowCount(0)
        
        # Add rows
        for log in logs:
            row = self.activities_table.rowCount()
            self.activities_table.insertRow(row)
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(log.timestamp)
                time_str = dt.strftime("%Y-%m-%d\n%H:%M:%S")
            except:
                time_str = log.timestamp
            
            # Add items to the row
            self.activities_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.activities_table.setItem(row, 1, QTableWidgetItem(log.action.replace('_', ' ').title()))
            self.activities_table.setItem(row, 2, QTableWidgetItem(log.roll_id if log.roll_id else "-"))
            
            # Format details
            details = []
            if isinstance(log.details, dict):
                for key, value in log.details.items():
                    details.append(f"{key}: {value}")
                details_text = "\n".join(details)
            else:
                details_text = str(log.details)
            
            self.activities_table.setItem(row, 3, QTableWidgetItem(details_text))
            
            # Color code based on action type
            color = None
            if 'error' in log.action.lower():
                color = QColor(255, 220, 220)  # Light red for errors
            elif 'cut' in log.action.lower():
                color = QColor(220, 230, 255)  # Light blue for cuts
            elif 'receive' in log.action.lower():
                color = QColor(220, 255, 220)  # Light green for receives
            
            if color:
                for col in range(self.activities_table.columnCount()):
                    item = self.activities_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(color))
