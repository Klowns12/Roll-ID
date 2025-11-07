from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtCharts import (
    QChart, QChartView, QBarSet, QBarSeries,
    QBarCategoryAxis, QValueAxis, QPieSeries
)

class StatisticsTab(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the Statistics tab UI"""
        layout = QVBoxLayout(self)
        
        # Date range selection
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_data)
        
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(self.refresh_btn)
        date_layout.addStretch()
        date_group.setLayout(date_layout)
        
        # Charts layout
        charts_layout = QHBoxLayout()
        
        # Roll by type chart
        self.roll_type_chart = self.create_chart("Rolls by Type")
        self.roll_type_view = QChartView(self.roll_type_chart)
        self.roll_type_view.setMinimumSize(400, 300)
        
        # Roll by status chart
        self.roll_status_chart = self.create_chart("Rolls by Status")
        self.roll_status_view = QChartView(self.roll_status_chart)
        self.roll_status_view.setMinimumSize(400, 300)
        
        charts_layout.addWidget(self.roll_type_view)
        charts_layout.addWidget(self.roll_status_view)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["Date", "SKU", "Type", "Quantity", "Status"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Add widgets to main layout
        layout.addWidget(date_group)
        layout.addLayout(charts_layout)
        layout.addWidget(QLabel("Detailed Data"))
        layout.addWidget(self.data_table)
    
    def create_chart(self, title):
        """Create a chart with the given title"""
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        return chart
    
    def load_data(self):
        """Load and display statistics data"""
        try:
            # Get date range
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().addDays(1).toString("yyyy-MM-dd")  # Add 1 day to include end date
            
            # TODO: Fetch data from storage based on date range
            # This is a placeholder - replace with actual data fetching
            roll_types = self.storage.get_roll_types_count(start_date, end_date)
            roll_statuses = self.storage.get_roll_statuses_count(start_date, end_date)
            
            # Update roll type chart
            self.update_pie_chart(self.roll_type_chart, roll_types)
            
            # Update roll status chart
            self.update_bar_chart(self.roll_status_chart, roll_statuses)
            
            # Update data table
            self.update_data_table(start_date, end_date)
            
        except Exception as e:
            print(f"Error loading statistics: {e}")
    
    def update_pie_chart(self, chart, data):
        """Update pie chart with data"""
        series = QPieSeries()
        for label, value in data.items():
            series.append(f"{label} ({value})", value)
        
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.setTitle(f"{chart.title()} - Total: {sum(data.values())}")
    
    def update_bar_chart(self, chart, data):
        """Update bar chart with data"""
        series = QBarSeries()
        bar_set = QBarSet("Count")
        
        categories = []
        for label, value in data.items():
            bar_set.append(value)
            categories.append(f"{label}\n({value})")
        
        series.append(bar_set)
        
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.setTitle(f"{chart.title()} - Total: {sum(data.values())}")
        
        # Customize axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis_x, series)
    
    def update_data_table(self, start_date, end_date):
        """Update the data table with detailed information"""
        try:
            # TODO: Fetch detailed data from storage
            # This is a placeholder - replace with actual data fetching
            data = self.storage.get_rolls_by_date_range(start_date, end_date)
            
            self.data_table.setRowCount(len(data))
            for row, item in enumerate(data):
                for col, value in enumerate(item):
                    self.data_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.data_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating data table: {e}")
