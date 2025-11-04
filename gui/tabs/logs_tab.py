from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QDateEdit, QComboBox, QGroupBox,
    QLineEdit, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QTextEdit, QToolTip, QApplication
)
from PySide6.QtCore import Qt, QDate, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator, QBrush, QColor
from datetime import datetime, timedelta
import json
import pandas as pd

class LogsTab(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        """Set up the Logs tab UI"""
        layout = QVBoxLayout(self)
        
        # Filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # Date range
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.dateChanged.connect(self.apply_filters)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.apply_filters)
        
        # Action type filter
        self.action_filter = QComboBox()
        self.action_filter.addItem("All Actions", "")
        self.action_filter.addItem("Roll Created", "roll_created")
        self.action_filter.addItem("Roll Updated", "roll_updated")
        self.action_filter.addItem("Roll Cut", "roll_cut")
        self.action_filter.addItem("Roll Deleted", "roll_deleted")
        self.action_filter.addItem("Master Added", "master_added")
        self.action_filter.addItem("Master Updated", "master_updated")
        self.action_filter.addItem("Master Deleted", "master_deleted")
        self.action_filter.addItem("Import", "import")
        self.action_filter.addItem("Export", "export")
        self.action_filter.currentIndexChanged.connect(self.apply_filters)
        
        # User filter
        self.user_filter = QLineEdit()
        self.user_filter.setPlaceholderText("Filter by user...")
        self.user_filter.textChanged.connect(self.apply_filters)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in details...")
        self.search_input.textChanged.connect(self.apply_filters)
        
        # Add to filter layout
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(QLabel("Action:"))
        filter_layout.addWidget(self.action_filter)
        filter_layout.addWidget(QLabel("User:"))
        filter_layout.addWidget(self.user_filter)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input, 1)  # Give search more space
        
        filter_group.setLayout(filter_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_logs)
        
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_logs)
        
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.clicked.connect(self.clear_logs)
        self.clear_btn.setStyleSheet("background-color: #ffcccc;")
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_btn)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Action", "User", "Roll ID", "Details"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.logs_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.logs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.logs_table.doubleClicked.connect(self.show_log_details)
        
        # Set column widths
        self.logs_table.setColumnWidth(0, 150)  # Timestamp
        self.logs_table.setColumnWidth(1, 150)  # Action
        self.logs_table.setColumnWidth(2, 100)  # User
        self.logs_table.setColumnWidth(3, 150)  # Roll ID
        # Details column will take remaining space
        
        # Add widgets to layout
        layout.addWidget(filter_group)
        layout.addLayout(btn_layout)
        layout.addWidget(self.logs_table, 1)  # Give table more space
    
    def load_logs(self):
        """Load logs from storage"""
        # Get all logs
        self.all_logs = self.storage.get_logs()
        
        # Apply filters
        self.apply_filters()
    
    def apply_filters(self):
        """Apply filters to the logs"""
        # Clear table
        self.logs_table.setRowCount(0)
        
        # Get filter values
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().addDays(1).toString("yyyy-MM-dd")  # Include end date
        action_filter = self.action_filter.currentData()
        user_filter = self.user_filter.text().lower()
        search_text = self.search_input.text().lower()
        
        # Filter logs
        filtered_logs = []
        for log in self.all_logs:
            # Skip if log doesn't have required attributes
            if not hasattr(log, 'timestamp') or not hasattr(log, 'action'):
                continue
            
            # Apply date filter
            if hasattr(log, 'timestamp'):
                log_date = log.timestamp.split('T')[0]  # Get date part only
                if log_date < start_date or log_date >= end_date:
                    continue
            
            # Apply action filter
            if action_filter and hasattr(log, 'action') and log.action != action_filter:
                continue
            
            # Apply user filter
            if user_filter and hasattr(log, 'user') and user_filter not in log.user.lower():
                continue
            
            # Apply search text filter
            if search_text:
                search_match = False
                
                # Check in action
                if hasattr(log, 'action') and search_text in log.action.lower():
                    search_match = True
                
                # Check in roll_id
                if not search_match and hasattr(log, 'roll_id') and log.roll_id and search_text in log.roll_id.lower():
                    search_match = True
                
                # Check in details
                if not search_match and hasattr(log, 'details'):
                    if isinstance(log.details, str) and search_text in log.details.lower():
                        search_match = True
                    elif isinstance(log.details, dict):
                        # Search in dictionary values
                        for value in log.details.values():
                            if search_text in str(value).lower():
                                search_match = True
                                break
                
                if not search_match:
                    continue
            
            filtered_logs.append(log)
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Add logs to table
        for log in filtered_logs:
            self.add_log_to_table(log)
        
        # Resize columns to contents
        self.logs_table.resizeColumnsToContents()
        # Make sure details column takes remaining space
        self.logs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
    
    def add_log_to_table(self, log):
        """Add a single log entry to the table"""
        row = self.logs_table.rowCount()
        self.logs_table.insertRow(row)
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            timestamp = str(log.timestamp)
        
        # Add cells
        self.logs_table.setItem(row, 0, QTableWidgetItem(timestamp))
        
        # Format action (make it more readable)
        action = getattr(log, 'action', '')
        action_display = action.replace('_', ' ').title()
        self.logs_table.setItem(row, 1, QTableWidgetItem(action_display))
        
        # User
        user = getattr(log, 'user', 'system')
        self.logs_table.setItem(row, 2, QTableWidgetItem(user))
        
        # Roll ID (with link style if available)
        roll_id = getattr(log, 'roll_id', '')
        roll_id_item = QTableWidgetItem(roll_id if roll_id else "N/A")
        if roll_id:
            roll_id_item.setForeground(QBrush(QColor(0, 0, 255)))  # Blue color for clickable
            roll_id_item.setData(Qt.ItemDataRole.UserRole, roll_id)  # Store roll ID for later use
        self.logs_table.setItem(row, 3, roll_id_item)
        
        # Details (truncated)
        details = getattr(log, 'details', '')
        if isinstance(details, dict):
            # Convert dict to formatted string
            details_str = ", ".join(f"{k}: {v}" for k, v in details.items())
        else:
            details_str = str(details)
        
        # Truncate long details
        max_length = 100
        if len(details_str) > max_length:
            details_str = details_str[:max_length] + "..."
        
        self.logs_table.setItem(row, 4, QTableWidgetItem(details_str))
        
        # Color code by action type
        self.color_code_row(row, action)
    
    def color_code_row(self, row, action):
        """Apply color coding based on action type"""
        if not action:
            return
        
        color = None
        
        # Define colors for different action types
        if 'error' in action:
            color = QColor(255, 220, 220)  # Light red for errors
        elif 'create' in action or 'add' in action:
            color = QColor(220, 255, 220)  # Light green for creation
        elif 'update' in action or 'edit' in action:
            color = QColor(220, 230, 255)  # Light blue for updates
        elif 'delete' in action or 'remove' in action:
            color = QColor(255, 240, 220)  # Light orange for deletions
        elif 'cut' in action:
            color = QColor(255, 255, 220)  # Light yellow for cuts
        
        # Apply background color to all cells in the row
        if color:
            for col in range(self.logs_table.columnCount()):
                item = self.logs_table.item(row, col)
                if item:
                    item.setBackground(color)
    
    def show_log_details(self, index):
        """Show detailed view of the selected log entry"""
        row = index.row()
        if row < 0 or row >= self.logs_table.rowCount():
            return
        
        # Get log data
        timestamp = self.logs_table.item(row, 0).text()
        action = self.logs_table.item(row, 1).text()
        user = self.logs_table.item(row, 2).text()
        roll_id = self.logs_table.item(row, 3).text()
        details = self.logs_table.item(row, 4).text()
        
        # Find the original log entry for full details
        log_entry = None
        for log in self.all_logs:
            log_roll_id = getattr(log, 'roll_id', '')
            log_timestamp = getattr(log, 'timestamp', '')
            
            if (str(log_roll_id) == roll_id and 
                timestamp.startswith(log_timestamp[:10])):
                log_entry = log
                break
        
        # Show details dialog
        dialog = LogDetailsDialog(
            timestamp=timestamp,
            action=action,
            user=user,
            roll_id=roll_id,
            details=log_entry.details if hasattr(log_entry, 'details') else details,
            parent=self
        )
        dialog.exec()
    
    def export_logs(self):
        """Export logs to CSV file"""
        if not self.all_logs:
            QMessageBox.information(self, "No Data", "There are no logs to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"fabric_roll_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Prepare data for export
            data = []
            for log in self.all_logs:
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    timestamp = str(getattr(log, 'timestamp', ''))
                
                # Format details
                details = getattr(log, 'details', '')
                if isinstance(details, dict):
                    details_str = json.dumps(details, ensure_ascii=False)
                else:
                    details_str = str(details)
                
                data.append({
                    'timestamp': timestamp,
                    'action': getattr(log, 'action', ''),
                    'user': getattr(log, 'user', 'system'),
                    'roll_id': getattr(log, 'roll_id', ''),
                    'details': details_str
                })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Successfully exported {len(data)} log entries to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting logs:\n{str(e)}"
            )
    
    def clear_logs(self):
        """Clear all logs (with confirmation)"""
        if not self.all_logs:
            QMessageBox.information(self, "No Logs", "There are no logs to clear.")
            return
        
        reply = QMessageBox.question(
            self,
            'Confirm Clear Logs',
            'Are you sure you want to delete all logs? This action cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # In a real implementation, you would call storage.clear_logs()
            # For now, we'll just show a message
            QMessageBox.information(
                self,
                "Clear Logs",
                "In a full implementation, all logs would be deleted here."
            )
            # self.load_logs()  # Refresh the table


class LogDetailsDialog(QDialog):
    """Dialog to display detailed log information"""
    def __init__(self, timestamp, action, user, roll_id, details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Details")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form layout for basic info
        form_layout = QFormLayout()
        
        self.timestamp_label = QLabel(timestamp)
        self.action_label = QLabel(action)
        self.user_label = QLabel(user)
        self.roll_id_label = QLabel(roll_id if roll_id != "N/A" else "N/A")
        
        form_layout.addRow("Timestamp:", self.timestamp_label)
        form_layout.addRow("Action:", self.action_label)
        form_layout.addRow("User:", self.user_label)
        form_layout.addRow("Roll ID:", self.roll_id_label)
        
        # Details text area
        details_label = QLabel("<b>Details:</b>")
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        
        # Format details
        if isinstance(details, dict):
            # Pretty print dictionary
            formatted_details = json.dumps(details, indent=2, ensure_ascii=False)
        else:
            formatted_details = str(details)
        
        self.details_text.setPlainText(formatted_details)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        
        # Add copy button
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_box.addButton(self.copy_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        # Add to layout
        layout.addLayout(form_layout)
        layout.addWidget(details_label)
        layout.addWidget(self.details_text, 1)  # Make details area expandable
        layout.addWidget(button_box)
    
    def copy_to_clipboard(self):
        """Copy details to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.details_text.toPlainText())
        
        # Show tooltip or status message
        QToolTip.showText(self.mapToGlobal(self.copy_btn.pos()), "Copied to clipboard!")
