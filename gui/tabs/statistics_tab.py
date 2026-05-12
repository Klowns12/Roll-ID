import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QFormLayout,
    QSizePolicy,
    QLineEdit,
    QRadioButton,
    QButtonGroup,
    QMessageBox,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSet,
    QBarSeries,
    QBarCategoryAxis,
    QValueAxis,
    QPieSeries,
)
import sys
import os
import math

from typing import List, Dict
from storage import Roll
from utils.master_suppliers_manager import MasterSuppliersManager

logger = logging.getLogger(__name__)


class StatisticsTab(QWidget):

    def __init__(self, storage):
        super().__init__()
        self.storage = storage

        # Initialize master suppliers manager
        root_dir = os.getcwd()

        self.rolls: List[Roll] = []
        self.suppliers_manager = MasterSuppliersManager()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Set up the Statistics tab UI"""
        layout = QVBoxLayout(self)

        # ===== FILTER SECTION =====
        filter_group = QGroupBox("ค้นหา / Search")
        filter_layout = QVBoxLayout()

        # Row 2: Suppliers, Code
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("Suppliers"))
        self.suppliers_input = QLineEdit()
        self.suppliers_input.setPlaceholderText("ค้นหา Suppliers...")
        self.suppliers_input.setMaximumWidth(250)
        self.suppliers_input.textChanged.connect(self.on_filters_changed)
        row2_layout.addWidget(self.suppliers_input)

        row2_layout.addSpacing(20)

        row2_layout.addWidget(QLabel("ค้นหา"))
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["Code", "Location", "Roll ID", "Lot"])
        self.search_field_combo.setMaximumWidth(140)
        self.search_field_combo.currentIndexChanged.connect(self.on_filters_changed)
        row2_layout.addWidget(self.search_field_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Code / Location / Roll ID / Lot")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.on_filters_changed)
        row2_layout.addWidget(self.search_input)

        row2_layout.addStretch()
        filter_layout.addLayout(row2_layout)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # ===== BUTTONS SECTION =====
        btn_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.setFixedSize(120, 30)
        self.export_btn.clicked.connect(self.export_to_excel)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedSize(80, 30)
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)

        # ===== DATA TABLE =====
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(11)
        self.data_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Roll ID",
                "SubPartCode",
                "SupCode",
                "Supplier Name",
                "Description",
                "Lot No.",
                "Location",
                "Unit",
                "Exist_Qty",
                "RollStatus",
            ]
        )
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setAlternatingRowColors(True)

        layout.addWidget(self.data_table)

        # ===== LOAD MORE BUTTON =====
        self.load_more_btn = QPushButton("More info (Load next 100)")
        self.load_more_btn.setFixedHeight(40)
        self.load_more_btn.clicked.connect(self.load_more_data)
        self.load_more_btn.setVisible(False)
        layout.addWidget(self.load_more_btn)

        # ===== PAYOUT HISTORY SECTION =====
        payout_group = QGroupBox("ประวัติการจ่าย / Dispatch History")
        payout_layout = QVBoxLayout()

        # Filter row
        payout_filter_layout = QHBoxLayout()

        self.show_all_payout_btn = QPushButton("แสดงประวัติทั้งหมด")
        self.show_all_payout_btn.clicked.connect(self.show_all_payout_history)
        payout_filter_layout.addWidget(self.show_all_payout_btn)

        payout_filter_layout.addSpacing(20)

        payout_filter_layout.addWidget(QLabel("กรอง LOT:"))
        self.payout_lot_input = QLineEdit()
        self.payout_lot_input.setPlaceholderText("กรอก LOT เพื่อค้นหา...")
        self.payout_lot_input.setMaximumWidth(200)
        payout_filter_layout.addWidget(self.payout_lot_input)

        self.payout_search_btn = QPushButton("ค้นหา")
        self.payout_search_btn.clicked.connect(self.load_payout_history)
        payout_filter_layout.addWidget(self.payout_search_btn)

        payout_filter_layout.addStretch()

        self.export_payout_btn = QPushButton("Export ประวัติส่ง")
        self.export_payout_btn.clicked.connect(self.export_payout_history)
        payout_filter_layout.addWidget(self.export_payout_btn)

        payout_layout.addLayout(payout_filter_layout)

        self.payout_table = QTableWidget()
        self.payout_table.setColumnCount(7)
        self.payout_table.setHorizontalHeaderLabels(
            ["วันที่", "Roll ID", "SKU", "LOT", "ลูกค้า", "เลขที่เอกสาร", "จำนวน"]
        )
        self.payout_table.horizontalHeader().setStretchLastSection(True)
        self.payout_table.setAlternatingRowColors(True)
        self.payout_table.setEditTriggers(QTableWidget.NoEditTriggers)

        payout_layout.addWidget(self.payout_table)
        payout_group.setLayout(payout_layout)
        layout.addWidget(payout_group)

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
            # โหลด rolls ทั้งหมดจาก database (ไม่ใช้ filter เพื่อป้องกันข้อมูลหายเมื่อ Refresh)
            if hasattr(self.storage, "search_rolls"):
                self.rolls = self.storage.search_rolls()
            elif hasattr(self.storage, "get_all_rolls"):
                self.rolls = self.storage.get_all_rolls()
            else:
                self.rolls = []

            logger.info(f"Loaded {len(self.rolls)} rolls from database")

            self.display_suppliers_data()
            self.load_payout_history()
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error loading statistics: {e}")

    def on_filters_changed(self, *_):
        """Handle any filter change"""
        self.display_suppliers_data()

    def display_suppliers_data(self):
        """Display combined supplier and roll data - CSV data has NO Roll ID, only storage.db data has Roll ID"""
        try:
            supplier_name = self.suppliers_input.text().strip()
            search_query = self.search_input.text().strip()
            search_field = self.search_field_combo.currentText()

            logger.info(f"Display suppliers data - supplier_name: {supplier_name}, search_query: {search_query}, search_field: {search_field}")

            supplier_records = self.suppliers_manager.search_combined(
                supplier_name, search_query
            )

            logger.info(f"Found {len(supplier_records)} supplier records")

            # Prepare roll lookups
            roll_by_id: Dict[str, Roll] = {}
            rolls_by_code: Dict[str, List[Roll]] = {}
            if self.rolls:
                for roll in self.rolls:
                    roll_by_id[roll.roll_id] = roll
                    code_key = roll.sku or roll.pdt_code or ""
                    if code_key:
                        rolls_by_code.setdefault(code_key, []).append(roll)

            logger.info(f"Prepared roll lookups - roll_by_id: {len(roll_by_id)}, rolls_by_code: {len(rolls_by_code)}")

            def matches_roll_filters(roll: Roll) -> bool:
                if (
                    supplier_name
                    and supplier_name.lower() not in (roll.spl_name or "").lower()
                ):
                    return False
                if not search_query:
                    return True
                target = ""
                if search_field == "Code":
                    target = roll.sku or roll.pdt_code or ""
                elif search_field == "Location":
                    target = roll.location or ""
                elif search_field == "Roll ID":
                    target = roll.roll_id or ""
                elif search_field == "Lot":
                    target = roll.lot or ""
                # Exact match (เท่านั้น ไม่ใช่ partial match)
                return search_query.lower() == str(target).lower()

            def matches_row_filters(row_data: Dict[str, str]) -> bool:
                if supplier_name:
                    supplier_text = str(
                        row_data.get("Supplier Name", row_data.get("Suppliers", ""))
                    ).lower()
                    if supplier_name.lower() not in supplier_text:
                        return False
                if not search_query:
                    return True
                if search_field == "Code":
                    target = row_data.get("Code", "")
                elif search_field == "Location":
                    target = row_data.get("Location", "")
                elif search_field == "Roll ID":
                    target = row_data.get("Roll ID", "")
                else:  # Lot
                    target = row_data.get("Lot No.", row_data.get("lot", ""))
                # Exact match (เท่านั้น ไม่ใช่ partial match)
                return search_query.lower() == str(target).lower()

            self.all_filtered_rows = []  # Store all rows here
            used_roll_ids: set[str] = set()

            search_type = "supplier" if supplier_name else "all"

            # Process CSV data (old data) - DO NOT create Roll IDs for them
            for record in supplier_records:
                row_data = self.suppliers_manager.get_row_data(record, search_type)
                if not matches_row_filters(row_data):
                    continue

                code_value = row_data.get("Code", "")

                exist_qty_value = 0.0
                roll_status_value = ""

                # Get data from Suppliers.csv
                qty_from_csv = row_data.get("QTY")
                full_rolls_from_csv = row_data.get("ม้วนเต็ม")
                scrap_from_csv = row_data.get("เศษ")

                # Get Exist_Qty from CSV
                if qty_from_csv is not None and str(qty_from_csv).strip():
                    try:
                        exist_qty_value = float(qty_from_csv)
                    except (ValueError, TypeError):
                        pass

                # Get RollStatus from CSV
                try:
                    full_val = (
                        float(full_rolls_from_csv)
                        if full_rolls_from_csv and str(full_rolls_from_csv).strip()
                        else 0
                    )
                    scrap_val = (
                        float(scrap_from_csv)
                        if scrap_from_csv and str(scrap_from_csv).strip()
                        else 0
                    )

                    # คำนวณสถานะจากข้อมูล CSV
                    if exist_qty_value <= 0:
                        roll_status_value = "หมด"
                    elif full_val > 0:
                        roll_status_value = "เต็มม้วน"
                    elif scrap_val > 0 or exist_qty_value > 0:
                        roll_status_value = "เศษ"
                except (ValueError, TypeError):
                    pass

                # Add CSV data row - Roll ID is EMPTY for old data
                self.all_filtered_rows.append(
                    {
                        "Code": row_data.get("Code", ""),
                        "Roll ID": "",  # DO NOT create Roll ID for CSV data
                        "SubPartCode": row_data.get("SubPartCode", ""),
                        "SupCode": row_data.get("SupCode", ""),
                        "Supplier Name": row_data.get(
                            "Supplier Name", row_data.get("Suppliers", "")
                        ),
                        "Description": row_data.get("Description", ""),
                        "Lot No.": row_data.get("Lot No.", row_data.get("lot", "")),
                        "Location": row_data.get("Location", ""),
                        "Unit": row_data.get("Unit", ""),
                        "Exist_Qty": (
                            f"{exist_qty_value:.2f}" if exist_qty_value is not None else ""
                        ),
                        "RollStatus": roll_status_value,
                    }
                )

            # Add NEW rolls from storage.db
            if self.rolls:
                for roll in self.rolls:
                    if not matches_roll_filters(roll):
                        continue

                    code_value = roll.sku or roll.pdt_code or ""

                    # สำหรับ rolls ใหม่ (มี Roll ID) ใช้ข้อมูลจาก database เป็นหลัก
                    # เพราะ CSV เป็นข้อมูลเก่าที่ไม่ได้อัปเดตตามการ dispatch
                    exist_qty_value = roll.current_length or 0.0

                    # คำนวณสถานะจาก database
                    if exist_qty_value <= 0:
                        roll_status_value = "หมด"
                    elif exist_qty_value >= (roll.original_length or 0.0):
                        roll_status_value = "เต็มม้วน"
                    else:
                        roll_status_value = "เศษ"

                    # ดึงข้อมูล supplier เฉพาะส่วนที่ไม่ใช่ Exist_Qty และ RollStatus
                    supplier_name = roll.spl_name or ""
                    try:
                        supplier_data = self.suppliers_manager.search_by_code(code_value)
                        if supplier_data:
                            # ดึงเฉพาะ supplier name จาก CSV ถ้าไม่มีใน roll
                            if not supplier_name:
                                supplier_name = str(supplier_data.get("Supplier Name", supplier_data.get("Suppliers", "")))
                    except:
                        pass

                    self.all_filtered_rows.append(
                        {
                            "Code": code_value,
                            "Roll ID": roll.roll_id,  # NEW data HAS Roll ID
                            "SubPartCode": roll.subpart_code or "",
                            "SupCode": roll.sup_code or "",
                            "Supplier Name": supplier_name,
                            "Description": roll.pdt_name or roll.specification or "",
                            "Lot No.": roll.lot or "",
                            "Location": roll.location or "",
                            "Unit": roll.unit_type or roll.packing_unit or "",
                            "Exist_Qty": (
                                f"{exist_qty_value:.2f}" if exist_qty_value is not None else ""
                            ),
                            "RollStatus": roll_status_value,
                        }
                    )

            # Reset pagination
            self.displayed_count = 0
            self.load_more_data()

            logger.info(f"Finished displaying suppliers data - total rows: {len(self.all_filtered_rows)}")

        except Exception as e:
            logger.error(f"Error displaying reports: {e}")
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error displaying reports: {e}")

    def load_more_data(self):
        """Load next batch of data"""
        batch_size = 100
        total_rows = len(self.all_filtered_rows)

        logger.info(f"Loading more data - displayed_count: {self.displayed_count}, total_rows: {total_rows}")

        if self.displayed_count >= total_rows:
            self.load_more_btn.setVisible(False)
            return

        next_count = min(self.displayed_count + batch_size, total_rows)
        rows_to_display = self.all_filtered_rows[:next_count]

        logger.info(f"Displaying {len(rows_to_display)} rows")

        self.display_table_data(rows_to_display)
        self.displayed_count = next_count

        # Update button visibility and text
        if self.displayed_count < total_rows:
            self.load_more_btn.setVisible(True)
            remaining = total_rows - self.displayed_count
            self.load_more_btn.setText(
                f"More info (Load next {min(batch_size, remaining)}) - Showing {self.displayed_count}/{total_rows}"
            )
        else:
            self.load_more_btn.setVisible(False)

    def export_to_excel(self):
        """Export current data to Excel (CSV format)"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv

            if not self.all_filtered_rows:
                QMessageBox.warning(self, "แจ้งเตือน", "ไม่มีข้อมูลที่จะ Export")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to Excel", "", "CSV Files (*.csv);;All Files (*)"
            )

            if not file_path:
                return

            headers = [
                "Code",
                "Roll ID",
                "SubPartCode",
                "SupCode",
                "Supplier Name",
                "Description",
                "Lot No.",
                "Location",
                "Unit",
                "Exist_Qty",
                "RollStatus",
            ]

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.all_filtered_rows)

            QMessageBox.information(
                self, "สำเร็จ", f"Export ข้อมูลเรียบร้อยแล้ว\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error exporting data: {e}")

    def display_table_data(self, rows: List[Dict[str, str]]):
        """Display rows in the table, preserving legacy columns and new metrics"""
        headers = [
            "Code",
            "Roll ID",
            "SubPartCode",
            "SupCode",
            "Supplier Name",
            "Description",
            "Lot No.",
            "Location",
            "Unit",
            "Exist_Qty",
            "RollStatus",
        ]
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)

        self.data_table.setRowCount(len(rows))
        for row_idx, data in enumerate(rows):
            for col_idx, header in enumerate(headers):
                value = data.get(header, "")
                item = QTableWidgetItem(str(value))
                if header == "RollStatus":
                    status_text = str(value).strip()
                    if status_text == "เต็มม้วน":
                        item.setForeground(Qt.darkGreen)
                    elif status_text:
                        item.setForeground(Qt.darkRed)
                self.data_table.setItem(row_idx, col_idx, item)

        self.data_table.resizeColumnsToContents()
        self.data_table.horizontalHeader().setStretchLastSection(True)

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

    def load_payout_history(self):
        """Load payout/dispatch history with LOT filter"""
        try:
            logs = self.storage.get_logs()
            dispatch_logs = [log for log in logs if log.action == "dispatch"]

            # Apply LOT filter
            lot_filter = self.payout_lot_input.text().strip()
            if lot_filter:
                dispatch_logs = [
                    log for log in dispatch_logs
                    if lot_filter.lower() in (log.details.get("lot", "")).lower()
                ]

            # Sort by timestamp descending
            dispatch_logs.sort(key=lambda x: x.timestamp, reverse=True)

            self.current_payout_logs = dispatch_logs

            self.payout_table.setRowCount(len(dispatch_logs))

            for row, log in enumerate(dispatch_logs):
                details = log.details

                # วันที่
                if isinstance(log.timestamp, str):
                    timestamp_str = log.timestamp
                else:
                    timestamp_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                self.payout_table.setItem(row, 0, QTableWidgetItem(timestamp_str))

                # Roll ID
                self.payout_table.setItem(row, 1, QTableWidgetItem(log.roll_id))

                # SKU
                self.payout_table.setItem(row, 2, QTableWidgetItem(details.get("sku", "")))

                # LOT
                self.payout_table.setItem(row, 3, QTableWidgetItem(details.get("lot", "")))

                # ลูกค้า (user)
                self.payout_table.setItem(row, 4, QTableWidgetItem(log.user))

                # เลขที่เอกสาร
                doc_no = details.get("doc_no", "")
                self.payout_table.setItem(row, 5, QTableWidgetItem(doc_no))

                # จำนวน (dispatch_length)
                dispatch_length = details.get("dispatch_length", "")
                self.payout_table.setItem(row, 6, QTableWidgetItem(dispatch_length))

            self.payout_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error loading payout history: {e}")

    def show_all_payout_history(self):
        """Clear LOT filter and show all payout history"""
        self.payout_lot_input.clear()
        self.load_payout_history()

    def export_payout_history(self):
        """Export payout history to CSV"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv

            if not getattr(self, "current_payout_logs", []):
                QMessageBox.warning(self, "แจ้งเตือน", "ไม่มีข้อมูลประวัติการจ่ายที่จะ Export")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export ประวัติการจ่าย", "", "CSV Files (*.csv);;All Files (*)"
            )
            if not file_path:
                return

            headers = ["วันที่", "Roll ID", "SKU", "LOT", "ลูกค้า", "เลขที่เอกสาร", "จำนวน"]

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for log in self.current_payout_logs:
                    if isinstance(log.timestamp, str):
                        ts = log.timestamp
                    else:
                        ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([
                        ts,
                        log.roll_id,
                        log.details.get("sku", ""),
                        log.details.get("lot", ""),
                        log.user,
                        log.details.get("doc_no", ""),
                        log.details.get("dispatch_length", ""),
                    ])

            QMessageBox.information(
                self, "สำเร็จ", f"Export ประวัติการจ่ายเรียบร้อยแล้ว\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error exporting payout history: {e}")

    def update_data_table(self, start_date, end_date):
        """Update the data table with detailed information"""
        try:
            # Fetch detailed data from storage
            data = self.storage.get_rolls_by_date_range(start_date, end_date)

            self.data_table.setRowCount(len(data))
            for row, item in enumerate(data):
                for col, value in enumerate(item):
                    self.data_table.setItem(row, col, QTableWidgetItem(str(value)))

            self.data_table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating data table: {e}")
