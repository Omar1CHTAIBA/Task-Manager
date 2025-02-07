import sys
import psutil
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QTabWidget
from PySide6.QtCore import QTimer, QPointF, QThread, Signal
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis

class SystemDataFetcher(QThread):
    update_process_data = Signal(list)
    update_cpu_usage = Signal(float)
    update_memory_usage = Signal(float)
    update_gpu_usage = Signal(float)
    update_network_usage = Signal(float)

    def run(self):
        while True:
            self.fetch_data()

    def fetch_data(self):
        # Fetch process data
        process_data = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            process_data.append([
                proc.info['pid'],
                proc.info['name'],
                proc.info['cpu_percent'],
                proc.info['memory_percent'],
                proc.info['memory_info'].rss / (1024 ** 3)
            ])
        self.update_process_data.emit(process_data)

        # Fetch CPU, Memory, GPU, and Network Usage
        self.update_cpu_usage.emit(psutil.cpu_percent(interval=1))
        self.update_memory_usage.emit(psutil.virtual_memory().percent)
        self.update_gpu_usage.emit(self.get_gpu_usage())
        self.update_network_usage.emit(self.get_network_usage())

    def get_gpu_usage(self):
        return 0

    def get_network_usage(self):
        return 0

class TaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Task Manager')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        self.tab_widget = QTabWidget()
        self.process_tab = QWidget()
        self.cpu_tab = QWidget()
        self.memory_tab = QWidget()
        self.gpu_tab = QWidget()
        self.network_tab = QWidget()

        self.create_process_tab()
        self.create_cpu_tab()
        self.create_memory_tab()
        self.create_gpu_tab()
        self.create_network_tab()

        self.tab_widget.addTab(self.process_tab, "Processes")
        self.tab_widget.addTab(self.cpu_tab, "CPU")
        self.tab_widget.addTab(self.memory_tab, "Memory")
        self.tab_widget.addTab(self.gpu_tab, "GPU")
        self.tab_widget.addTab(self.network_tab, "Network")

        self.layout.addWidget(self.tab_widget)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Create and start the worker thread
        self.worker_thread = SystemDataFetcher()
        self.worker_thread.start()

        # Connect signals to update methods
        self.worker_thread.update_process_data.connect(self.update_process_table)
        self.worker_thread.update_cpu_usage.connect(self.update_cpu_chart)
        self.worker_thread.update_memory_usage.connect(self.update_memory_chart)
        self.worker_thread.update_gpu_usage.connect(self.update_gpu_chart)
        self.worker_thread.update_network_usage.connect(self.update_network_chart)

    def create_process_tab(self):
        layout = QVBoxLayout()
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(['PID', 'Process Name', 'CPU %', 'Memory %', 'Memory (GB)'])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.process_table)
        self.process_tab.setLayout(layout)

    def create_chart_tab(self, tab, series_name):
        layout = QVBoxLayout()
        self.chart = QChart()
        series = QLineSeries()
        series.setName(series_name)
        self.chart.addSeries(series)
        self.chart.createDefaultAxes()
        axisX = QValueAxis()
        axisY = QValueAxis()
        axisY.setRange(0, 100)  # Set y-axis range to 0-100 for percentages
        self.chart.setAxisX(axisX, series)
        self.chart.setAxisY(axisY, series)
        self.chart_view = QChartView(self.chart)
        layout.addWidget(self.chart_view)
        tab.setLayout(layout)
        return series

    def create_cpu_tab(self):
        self.cpu_series = self.create_chart_tab(self.cpu_tab, "CPU Usage")

    def create_memory_tab(self):
        self.memory_series = self.create_chart_tab(self.memory_tab, "Memory Usage")

    def create_gpu_tab(self):
        self.gpu_series = self.create_chart_tab(self.gpu_tab, "GPU Usage")

    def create_network_tab(self):
        self.network_series = self.create_chart_tab(self.network_tab, "Network Usage")

    def update_process_table(self, process_data):
        self.process_table.setRowCount(0)
        for data in process_data:
            row_position = self.process_table.rowCount()
            self.process_table.insertRow(row_position)
            for col, value in enumerate(data):
                self.process_table.setItem(row_position, col, QTableWidgetItem(f"{value:.2f}" if isinstance(value, float) else str(value)))

    def update_cpu_chart(self, cpu_usage):
        self.update_chart_series(self.cpu_series, cpu_usage)

    def update_memory_chart(self, memory_usage):
        self.update_chart_series(self.memory_series, memory_usage)

    def update_gpu_chart(self, gpu_usage):
        self.update_chart_series(self.gpu_series, gpu_usage)

    def update_network_chart(self, network_usage):
        self.update_chart_series(self.network_series, network_usage)

    def update_chart_series(self, series, value):
        points = series.pointsVector()
        if len(points) > 100:  # Keep only the last 100 data points
            points.pop(0)
        points.append(QPointF(len(points), value))
        series.replace(points)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    task_manager = TaskManager()
    task_manager.show()
    sys.exit(app.exec())