import os
import sys
import asyncio
import aiohttp
import pandas as pd
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt
import webbrowser


# Async function to fetch CVE data
async def fetch(session, base_url, cve):
    url = f"{base_url}{cve}"
    async with session.get(url) as response:
        if response.status == 200:
            return cve, await response.json()
        else:
            print(f"Failed to call API for CVE {cve}. Status code:", response.status)
            return cve, None


# Async function to call the API and merge data
async def call_api_with_cve_and_merge(base_url, input_file, output_file, status_label):
    try:
        cve_data = pd.read_csv(input_file)
        cve_values = cve_data['CVE'].astype(str).tolist()

        results = {}

        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, base_url, cve) for cve in cve_values]
            for future in asyncio.as_completed(tasks):
                cve, result = await future
                if result:
                    results[cve] = result['data']

        for key in results:
            data = results[key]
            for item in data:
                for k, v in item.items():
                    cve_data.loc[cve_data['CVE'] == key, f"{k}"] = v

        cve_data.to_csv(output_file, index=False)

        status_label.setText("Saved In: " + output_file)
        return True
    except Exception as e:
        status_label.setText(f"Error: {str(e)}")
        return False


# Main GUI class
class CVEGui(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EPSS App")
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.setGeometry(100, 100, 700, 400)
        self.setAcceptDrops(True)

        self.initUI()

    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Input File Layout
        input_layout = QHBoxLayout()
        self.input_file_label = QLabel("Input CSV File:")
        self.input_file_entry = QLineEdit()
        self.input_file_entry.setPlaceholderText("Drag and drop a CSV file here or click 'Browse'...")
        self.input_file_button = QPushButton("Browse")
        self.input_file_button.setStyleSheet(self.get_dark_blue_button_style())
        self.input_file_button.clicked.connect(self.browse_input_file)
        input_layout.addWidget(self.input_file_label)
        input_layout.addWidget(self.input_file_entry)
        input_layout.addWidget(self.input_file_button)

        # Output Folder Layout
        output_layout = QHBoxLayout()
        self.output_folder_label = QLabel("Output Folder:")
        self.output_folder_entry = QLineEdit()
        self.output_folder_entry.setPlaceholderText("Select a folder to save the output file...")
        self.output_folder_button = QPushButton("Browse")
        self.output_folder_button.setStyleSheet(self.get_dark_blue_button_style())
        self.output_folder_button.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_folder_label)
        output_layout.addWidget(self.output_folder_entry)
        output_layout.addWidget(self.output_folder_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # Start Processing Button
        self.start_button = QPushButton("Start Processing")
        self.start_button.setStyleSheet(self.get_dark_blue_button_style())
        self.start_button.clicked.connect(self.start_processing)

        # Open File Button (hidden initially)
        self.open_file_button = QPushButton("Open File")
        self.open_file_button.setStyleSheet(self.get_dark_blue_button_style())
        self.open_file_button.clicked.connect(self.open_output_file)
        self.open_file_button.setVisible(False)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Add layouts to main layout
        main_layout.addLayout(input_layout)
        main_layout.addLayout(output_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(self.open_file_button)
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def get_dark_blue_button_style(self):
        """Returns the dark blue button style with gradient and hover effects."""
        return """
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #003366, stop: 1 #00509e
                );
                color: white;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #00294d, stop: 1 #004080
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #001f33, stop: 1 #003366
                );
            }
        """

    def browse_input_file(self):
        options = QFileDialog.Options()
        input_file_path, _ = QFileDialog.getOpenFileName(self, "Select Input CSV File", "", "CSV Files (*.csv)", options=options)
        if input_file_path:
            self.input_file_entry.setText(input_file_path)

    def browse_output_folder(self):
        options = QFileDialog.Options()
        output_folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder", "", options=options)
        if output_folder_path:
            self.output_folder_entry.setText(output_folder_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith('.csv'):
                if not self.input_file_entry.text():
                    self.input_file_entry.setText(file_path)
                else:
                    self.output_folder_entry.setText(os.path.dirname(file_path))

    def start_processing(self):
        base_url = 'https://api.first.org/data/v1/epss?cve='
        input_file = self.input_file_entry.text()
        output_folder = self.output_folder_entry.text()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.warning(self, "Error", "Please select a valid input CSV file.")
            return
        if not output_folder or not os.path.isdir(output_folder):
            QMessageBox.warning(self, "Error", "Please select a valid output folder.")
            return

        # Generate output file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(output_folder, f"output_{timestamp}.csv")

        self.status_label.setText("Processing...")
        self.progress_bar.setValue(0)
        self.open_file_button.setVisible(False)

        threading.Thread(target=self.run_async_processing, args=(base_url, input_file, self.output_file)).start()

    def run_async_processing(self, base_url, input_file, output_file):
        result = asyncio.run(call_api_with_cve_and_merge(base_url, input_file, output_file, self.status_label))
        if result:
            self.progress_bar.setValue(100)
            self.open_file_button.setVisible(True)

    def open_output_file(self):
        if self.output_file and os.path.exists(self.output_file):
            webbrowser.open(self.output_file)
        else:
            QMessageBox.warning(self, "Error", "The output file could not be found.")


# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CVEGui()
    window.show()
    sys.exit(app.exec_())
