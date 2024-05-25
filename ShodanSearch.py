import subprocess
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import shodan
import pandas as pd

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ["shodan", "pandas"]

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

def run_shodan_search():
    SHODAN_API_KEY = "2bkjIJvPmBailFOwRqvbrNjSGp1cRtG9"
    api = shodan.Shodan(SHODAN_API_KEY)

    search_query = search_entry.get()
    output_file = output_entry.get()

    if not output_file.endswith('.csv'):
        output_file += '.csv'

    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file_path = os.path.join(current_dir, output_file)

    try:
        results = api.search(search_query)
        
        if not results['matches']:
            messagebox.showinfo("No Results", "No results found for the given search query.")
            return

        data = []
        for result in results['matches']:
            item = {
                'IP': result.get('ip_str', ''),
                'Port': result.get('port', ''),
                'Hostnames': result.get('hostnames', []),
                'Location': result.get('location', {}),
                'ISP': result.get('isp', ''),
                'Organization': result.get('org', ''),
                'Operating System': result.get('os', ''),
                'Timestamp': result.get('timestamp', ''),
                'Data': result.get('data', '')
            }
            data.append(item)

        df = pd.DataFrame(data)

        if not df.empty:
            location_df = pd.json_normalize(df['Location'])
            df = pd.concat([df.drop(columns='Location'), location_df], axis=1)

        df.to_csv(output_file_path, index=False)
        messagebox.showinfo("Success", f"Data successfully exported to {output_file_path}")

    except shodan.APIError as e:
        messagebox.showerror("API Error", f"Error: {e}")

root = tk.Tk()
root.title("Shodan Search Tool")
root.configure(bg="#004578")  # Set the background color


root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(3, weight=1)


def on_enter(e):
    search_button.config(background='green')

def on_leave(e):
    search_button.config(background='SystemButtonFace')


tk.Label(root, text="Enter the search query for Shodan:", bg="#004578", fg="white").grid(row=0, column=0, padx=10, pady=5, sticky='e')
search_entry = tk.Entry(root, width=50)
search_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

tk.Label(root, text="Enter the output CSV file name (with .csv extension):", bg="#004578", fg="white").grid(row=1, column=0, padx=10, pady=5, sticky='e')
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')

search_button = tk.Button(root, text="Search", command=run_shodan_search)
search_button.grid(row=2, column=0, columnspan=2, pady=10)


search_button.bind("<Enter>", on_enter)
search_button.bind("<Leave>", on_leave)


for widget in root.winfo_children():
    widget.grid_configure(padx=5, pady=5)


root.grid_rowconfigure(2, weight=1)
search_button.grid(row=2, column=0, columnspan=2)

root.mainloop()
