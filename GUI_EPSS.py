import subprocess
import sys

# List of required libraries
required_libraries = [
    'aiohttp',      # For asynchronous HTTP requests
    'pandas',       # For handling CSV data
    'pyqt5',        # For GUI components
    'pyinstaller'   # For creating the .exe file
]

# Install each library
for lib in required_libraries:
    try:
        __import__(lib)
        print(f"{lib} is already installed.")
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

print("All required libraries are installed!")
