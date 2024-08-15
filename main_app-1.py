import sys
import pandas as pd
import requests
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTextBrowser, QProgressBar, 
)
from PyQt5.QtCore import pyqtSignal, QThread, Qt
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
import urllib3
from screenshot_tool import ScreenshotTool  
from PyQt5.QtWidgets import QSplashScreen, QProgressBar
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a pixmap with a black background for the splash screen
        pixmap = QPixmap(400, 200)  # Adjust width and height as needed
        pixmap.fill(Qt.black)
        
        super().__init__(pixmap)
        self.setMask(pixmap.mask())
        
        # Create and configure progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 170, 300, 20)  # Adjusted position for better fit
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 10px;
                background-color: #444;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #E0E0E0;
                border-radius: 10px;
            }
        """)
        self.progress_bar.setValue(0)

        # Create QLabel for GIF and adjust its size to fit the splash screen
        self.gif_label = QLabel(self)
        self.gif_label.setGeometry(0, 0, 400, 160)  # Set to match splash screen width and a height
        self.gif_label.setAlignment(Qt.AlignCenter)

        # Determine the path to the GIF file
        if getattr(sys, 'frozen', False):
            # If running as a bundled executable
            base_path = sys._MEIPASS
        else:
            # If running in a normal Python environment
            base_path = os.path.dirname(__file__)
        
        gif_path = os.path.join(base_path, 'splashscreen', 'phir-hera-pheri-raju.gif')
        
        # Load and start the GIF
        self.movie = QMovie(gif_path)
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        
        # Timer to simulate loading progress
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)  # Update progress every 30 ms
        self.progress_value = 0

    def update_progress(self):
        self.progress_value += 1
        self.progress_bar.setValue(self.progress_value)
        if self.progress_value >= 100:
            self.timer.stop()
            self.close()

class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            self.func(*self.args, self.log_signal.emit, self.done_signal.emit, self.progress_signal.emit)
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")

def check_http_https_services(host_or_ip, ports, log_callback):
    results = []
    for port in ports:
        try:
            url = f"http://{host_or_ip}:{port}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                results.append((url, 'yellow'))
                log_callback(f"HTTP OK: {url}<br>")
        except requests.RequestException:
            pass

        try:
            url = f"https://{host_or_ip}:{port}"
            response = requests.get(url, timeout=3, verify=False)
            if response.status_code == 200:
                results.append((url, 'green'))
                log_callback(f"HTTPS OK: {url}<br>")
        except requests.RequestException:
            pass

    return results

def check_http_https_services_vm(fqdn_or_host, port, log_callback):
    results = []
    try:
        url = f"http://{fqdn_or_host}:{port}"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            results.append((url, 'yellow'))
            log_callback(f"HTTP OK: {url}<br>")
    except requests.RequestException:
        pass

    try:
        url = f"https://{fqdn_or_host}:{port}"
        response = requests.get(url, timeout=3, verify=False)
        if response.status_code == 200:
            results.append((url, 'green'))
            log_callback(f"HTTPS OK: {url}<br>")
    except requests.RequestException:
        pass

    return results

def process_csv_asm(input_csv, output_csv, log_callback, completion_callback, progress_callback):
    if not os.path.isfile(input_csv):
        log_callback(f"Error: The file '{input_csv}' does not exist.<br>")
        return

    df = pd.read_csv(input_csv)
    total_entries = len(df)
    results = []

    for index, row in df.iterrows():
        host = row['Host']
        ip = row['IP']
        ports_str = row['Ports']

        addresses = []
        if pd.notna(host):
            addresses.append(host)
        if pd.notna(ip):
            addresses.append(ip)

        if not addresses:
            log_callback(f"Skipping entry {index + 1} with missing Host and IP.<br>")
            continue

        try:
            ports = eval(ports_str) if pd.notna(ports_str) else []
            if not isinstance(ports, list):
                ports = [ports]
        except Exception as e:
            log_callback(f"Error processing ports for entry {index + 1}: {e}<br>")
            continue

        log_callback(f"Processing entry {index + 1} of {total_entries}: Host={host}, IP={ip}, Ports={ports}<br>")

        for address in addresses:
            valid_urls = check_http_https_services(address, ports, log_callback)
            for url, color in valid_urls:
                results.append({'Host': host, 'IP': ip, 'Port': ports_str, 'URL': url})

        progress_callback(int((index + 1) / total_entries * 100))
        results.append({'Host': '', 'IP': '', 'Port': '', 'URL': ''})

    result_df = pd.DataFrame(results)
    try:
        result_df.to_csv(output_csv, index=False)
        log_callback(f"Results saved to {output_csv}<br>")
        completion_callback(f"Results saved to {output_csv}")
    except Exception as e:
        log_callback(f"Error saving results to {output_csv}: {e}<br>")
        completion_callback(f"Error saving results to {output_csv}: {e}")

def process_csv_vm(input_csv, output_csv, log_callback, completion_callback, progress_callback):
    if not os.path.isfile(input_csv):
        log_callback(f"Error: The file '{input_csv}' does not exist.<br>")
        return

    df = pd.read_csv(input_csv)
    total_entries = len(df)
    results = []

    for index, row in df.iterrows():
        fqdn = row.get('FQDN')
        host = row.get('Host')
        port_str = row.get('Port')

        if pd.isna(fqdn) and pd.isna(host):
            log_callback(f"Skipping entry {index + 1} with missing FQDN and Host.<br>")
            continue

        try:
            ports = str(port_str).split(',') if pd.notna(port_str) else []
            ports = [port.strip() for port in ports]
        except Exception as e:
            log_callback(f"Error processing port for entry {index + 1}: {e}<br>")
            continue

        log_callback(f"Processing entry {index + 1} of {total_entries}: FQDN={fqdn}, Host={host}, Port={ports}<br>")

        for port in ports:
            for address in [fqdn, host]:
                if pd.notna(address):  # Ensure address is not NaN
                    valid_urls = check_http_https_services_vm(address, port, log_callback)
                    for url, color in valid_urls:
                        results.append({'FQDN': fqdn, 'Host': host, 'Port': port, 'URL': url})

        progress_callback(int((index + 1) / total_entries * 100))
        results.append({'FQDN': '', 'Host': '', 'Port': '', 'URL': ''})

    result_df = pd.DataFrame(results)
    try:
        result_df.to_csv(output_csv, index=False)
        log_callback(f"Results saved to {output_csv}<br>")
        completion_callback(f"Results saved to {output_csv}")
    except Exception as e:
        log_callback(f"Error saving results to {output_csv}: {e}<br>")
        completion_callback(f"Error saving results to {output_csv}: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Internet Facing Portals Scanning Tool")
        self.setGeometry(100, 100, 900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.setStyleSheet("background-color: #000000;")  # Set the main window background to black

        self.title_label = QLabel("Internet Facing Portals Scanning Tool", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.title_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20)
        self.layout.addLayout(self.button_layout)

        self.asm_button = QPushButton("ASM", self)
        self.asm_button.setIcon(QIcon('path/to/asm_icon.png'))  # Add your icon path here
        self.asm_button.setStyleSheet("background-color: #333; color: #E0E0E0; font-size: 16px; border-radius: 8px; padding: 12px;")
        self.asm_button.clicked.connect(self.show_asm_interface)
        self.button_layout.addWidget(self.asm_button)

        self.vm_button = QPushButton("VM", self)
        self.vm_button.setIcon(QIcon('path/to/vm_icon.png'))  # Add your icon path here
        self.vm_button.setStyleSheet("background-color: #333; color: #E0E0E0; font-size: 16px; border-radius: 8px; padding: 12px;")
        self.vm_button.clicked.connect(self.show_vm_interface)
        self.button_layout.addWidget(self.vm_button)

        self.screenshot_button = QPushButton("Screenshot Tool", self)
        self.screenshot_button.setStyleSheet("background-color: #333; color: #E0E0E0; font-size: 16px; border-radius: 8px; padding: 12px;")
        self.screenshot_button.clicked.connect(self.open_screenshot_tool)
        self.button_layout.addWidget(self.screenshot_button)

        self.log_browser = QTextBrowser(self)
        self.log_browser.setOpenExternalLinks(True)
        self.log_browser.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444;")
        self.layout.addWidget(self.log_browser)

    def show_asm_interface(self):
        self.asm_window = ASMWindow()
        self.asm_window.show()

    def show_vm_interface(self):
        self.vm_window = VMWindow()
        self.vm_window.show()

    def open_screenshot_tool(self):
        self.screenshot_tool_window = ScreenshotTool()  # Instantiate and show the ScreenshotTool window
        self.screenshot_tool_window.show()

class ASMWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASM Processing")
        self.setGeometry(100, 100, 900, 700)


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.setStyleSheet("background-color: #000000;")  # Set the main window background to black

        self.title_label = QLabel("ASM Processing", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.title_label)

        self.input_label = QLabel("Input CSV File:", self)
        self.input_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.input_label)

        self.input_line_edit = QLineEdit(self)
        self.input_line_edit.setPlaceholderText("Enter input CSV file path")
        self.input_line_edit.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444; padding: 10px;")
        self.layout.addWidget(self.input_line_edit)

        self.browse_input_button = QPushButton("Browse", self)
        self.browse_input_button.setStyleSheet("background-color: #1e88e5; color: #fff; padding: 10px; border-radius: 5px;")
        self.browse_input_button.clicked.connect(self.browse_input)
        self.layout.addWidget(self.browse_input_button)

        self.output_label = QLabel("Output CSV File:", self)
        self.output_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.output_label)

        self.output_line_edit = QLineEdit(self)
        self.output_line_edit.setPlaceholderText("Enter output CSV file path")
        self.output_line_edit.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444; padding: 10px;")
        self.layout.addWidget(self.output_line_edit)

        self.browse_output_button = QPushButton("Browse", self)
        self.browse_output_button.setStyleSheet("background-color: #1e88e5; color: #fff; padding: 10px; border-radius: 5px;")
        self.browse_output_button.clicked.connect(self.browse_output)
        self.layout.addWidget(self.browse_output_button)

        self.start_button = QPushButton("Start Processing", self)
        self.start_button.setStyleSheet("background-color: #ff5722; color: #fff; padding: 10px; border-radius: 5px;")
        self.start_button.clicked.connect(self.start_processing_asm)
        self.layout.addWidget(self.start_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 10px;
                background-color: #444;
                text-align: center;
                color: #faf5f5;
                padding: 5px; 
                font-weight: bold;                         
                font-size: 14px;                    
            }
            QProgressBar::chunk {
                background-color: #007A8E;
                border-radius: 10px;
            }
        """)
        self.layout.addWidget(self.progress_bar)


        self.log_browser = QTextBrowser(self)
        self.log_browser.setOpenExternalLinks(True)
        self.log_browser.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444;")
        self.layout.addWidget(self.log_browser)

    def browse_input(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.input_line_edit.setText(file_name)

    def browse_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Select Output CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.output_line_edit.setText(file_name)

    def start_processing_asm(self):
        input_csv = self.input_line_edit.text()
        output_csv = self.output_line_edit.text()
        if not input_csv or not output_csv:
            self.log_browser.append("Error: Please specify both input and output file paths.")
            return

        self.worker_thread = WorkerThread(process_csv_asm, input_csv, output_csv)
        self.worker_thread.log_signal.connect(self.log_browser.append)
        self.worker_thread.done_signal.connect(self.log_browser.append)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.start()

class VMWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VM Processing")
        self.setGeometry(100, 100, 900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.setStyleSheet("background-color: #000000;")  # Set the main window background to black

        self.title_label = QLabel("VM Processing", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.title_label)

        self.input_label = QLabel("Input CSV File:", self)
        self.input_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.input_label)

        self.input_line_edit = QLineEdit(self)
        self.input_line_edit.setPlaceholderText("Enter input CSV file path")
        self.input_line_edit.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444; padding: 10px;")
        self.layout.addWidget(self.input_line_edit)

        self.browse_input_button = QPushButton("Browse", self)
        self.browse_input_button.setStyleSheet("background-color: #1e88e5; color: #fff; padding: 10px; border-radius: 5px;")
        self.browse_input_button.clicked.connect(self.browse_input)
        self.layout.addWidget(self.browse_input_button)

        self.output_label = QLabel("Output CSV File:", self)
        self.output_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.output_label)

        self.output_line_edit = QLineEdit(self)
        self.output_line_edit.setPlaceholderText("Enter output CSV file path")
        self.output_line_edit.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444; padding: 10px;")
        self.layout.addWidget(self.output_line_edit)

        self.browse_output_button = QPushButton("Browse", self)
        self.browse_output_button.setStyleSheet("background-color: #1e88e5; color: #fff; padding: 10px; border-radius: 5px;")
        self.browse_output_button.clicked.connect(self.browse_output)
        self.layout.addWidget(self.browse_output_button)

        self.start_button = QPushButton("Start Processing", self)
        self.start_button.setStyleSheet("background-color: #ff5722; color: #fff; padding: 10px; border-radius: 5px;")
        self.start_button.clicked.connect(self.start_processing_vm)
        self.layout.addWidget(self.start_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 10px;
                background-color: #444;
                text-align: center;
                color: #faf5f5;
                padding: 5px; 
                font-weight: bold;                         
                font-size: 14px;                    
            }
            QProgressBar::chunk {
                background-color: #007A8E;
                border-radius: 10px;
            }
        """)
        self.layout.addWidget(self.progress_bar)


        self.log_browser = QTextBrowser(self)
        self.log_browser.setOpenExternalLinks(True)
        self.log_browser.setStyleSheet("background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444;")
        self.layout.addWidget(self.log_browser)

    def browse_input(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.input_line_edit.setText(file_name)

    def browse_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Select Output CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.output_line_edit.setText(file_name)

    def start_processing_vm(self):
        input_csv = self.input_line_edit.text()
        output_csv = self.output_line_edit.text()
        if not input_csv or not output_csv:
            self.log_browser.append("Error: Please specify both input and output file paths.")
            return

        self.worker_thread = WorkerThread(process_csv_vm, input_csv, output_csv)
        self.worker_thread.log_signal.connect(self.log_browser.append)
        self.worker_thread.done_signal.connect(self.log_browser.append)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.start()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Page")
        self.setGeometry(100, 100, 900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.setStyleSheet("background-color: #000000;")  # Set the main window background to black

        self.title_label = QLabel("Hello Guys!!", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.title_label)

        self.asm_button = QPushButton("ASM Processing", self)
        self.asm_button.setStyleSheet("background-color: #4CAF50; color: #E0E0E0; font-size: 16px; border-radius: 8px; padding: 12px;")
        self.asm_button.clicked.connect(self.open_asm_window)
        self.layout.addWidget(self.asm_button)

        self.vm_button = QPushButton("VM Processing", self)
        self.vm_button.setStyleSheet("background-color: #4CAF50; color: #E0E0E0; font-size: 16px; border-radius: 8px; padding: 12px;")
        self.vm_button.clicked.connect(self.open_vm_window)
        self.layout.addWidget(self.vm_button)

        self.screenshot_button = QPushButton("Screenshots", self)
        self.screenshot_button.setStyleSheet("background-color: #4CAF50; color: #E0E0E0; font-size: 16px; border-radius: 8px; padding: 12px;")
        self.screenshot_button.clicked.connect(self.open_screenshot_tool)
        self.layout.addWidget(self.screenshot_button)

    def open_asm_window(self):
        self.asm_window = ASMWindow()
        self.asm_window.show()

    def open_vm_window(self):
        self.vm_window = VMWindow()
        self.vm_window.show()

    def open_screenshot_tool(self):
        # Add the logic to open the ScreenshotTool window
        self.screenshot_window = ScreenshotTool()
        self.screenshot_window.show()
      

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the splash screen
    splash = SplashScreen()
    splash.show()

    # Create the main window
    main_window = MainWindow()

    # Show the main window after the splash screen
    QTimer.singleShot(3000, lambda: main_window.show())  # Show main window after 3 seconds

    sys.exit(app.exec_())
