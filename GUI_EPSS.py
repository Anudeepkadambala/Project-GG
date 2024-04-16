import os
import subprocess
import sys
import asyncio
import aiohttp
import pandas as pd
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

def install_required_libraries():
    required_libraries = ['aiohttp', 'pandas', 'json']

    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

install_required_libraries()

async def fetch(session, base_url, cve):
    url = f"{base_url}{cve}"
    async with session.get(url) as response:
        if response.status == 200:
            return cve, await response.json()
        else:
            print(f"Failed to call API for CVE {cve}. Status code:", response.status)
            return cve, None

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

        
        cve_data.drop(columns=['cve'], inplace=True)

        
        cve_data.to_csv(output_file, index=False)

        status_label.config(text="Saved In : " + output_file, fg="White")
    except Exception as e:
        status_label.config(text="Error: " + str(e), fg="red")


def run_script_with_gui():
    def browse_input_file():
        input_file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        input_file_entry.delete(0, tk.END)
        input_file_entry.insert(0, input_file_path)

    def browse_output_file():
        output_file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        output_file_entry.delete(0, tk.END)
        output_file_entry.insert(0, output_file_path)

    def start_processing():
        base_url = 'https://api.first.org/data/v1/epss?cve='
        input_file = input_file_entry.get()
        output_file = output_file_entry.get()

        if not input_file:
            messagebox.showerror("Error", "Please select an input CSV file.")
            return
        if not output_file:
            messagebox.showerror("Error", "Please enter the output CSV file name.")
            return

        status_label.config(text="Processing...", fg="black")
        asyncio.run(call_api_with_cve_and_merge(base_url, input_file, output_file, status_label))

    def on_resize(event):
        
        window.update_idletasks()
        window_width = window.winfo_width()
        window_height = window.winfo_height()

        input_frame.place(relx=0.5, rely=0.3, anchor="center")
        output_frame.place(relx=0.5, rely=0.5, anchor="center")
        start_button.place(relx=0.5, rely=0.7, anchor="center")
        status_label.place(relx=0.5, rely=0.85, anchor="center")

    def on_enter(event):
        event.widget.config(bg="#145A32")

    def on_leave(event):
        event.widget.config(bg="#4CAF50")

  
    window = tk.Tk()
    window.title("GG EPSS APP")
    window.configure(bg="#004578")

    bg_canvas = tk.Canvas(window, width=800, height=300, bg="#085899", highlightthickness=0)
    bg_canvas.grid(row=0, column=0, columnspan=3)
    bg_canvas.create_rectangle(0, 0, 800, 300, fill="#004578", outline="")

    input_frame = tk.Frame(window, bg="#004578")
    input_frame.place(relx=0.5, rely=0.3, anchor="center")
    input_file_label = tk.Label(input_frame, text="Input CSV File:", bg="#004578", fg="white", font=("Helvetica", 12))
    input_file_label.pack(side=tk.LEFT, padx=10, pady=5)
    input_file_entry = tk.Entry(input_frame, width=50, bg="#ffffff", bd=1, relief="solid", font=("Helvetica", 10))
    input_file_entry.pack(side=tk.LEFT, padx=5, pady=5)
    input_file_button = tk.Button(input_frame, text="Browse", command=browse_input_file, bg="#4CAF50", fg="white", font=("Helvetica", 10))
    input_file_button.pack(side=tk.LEFT, padx=5, pady=5)
    input_file_button.bind("<Enter>", on_enter)
    input_file_button.bind("<Leave>", on_leave)

    output_frame = tk.Frame(window, bg="#004578")
    output_frame.place(relx=0.5, rely=0.5, anchor="center")
    output_file_label = tk.Label(output_frame, text="Output CSV File:", bg="#004578", fg="white", font=("Helvetica", 12))
    output_file_label.pack(side=tk.LEFT, padx=10, pady=5)
    output_file_entry = tk.Entry(output_frame, width=50, bg="#ffffff", bd=1, relief="solid", font=("Helvetica", 10))
    output_file_entry.pack(side=tk.LEFT, padx=5, pady=5)
    output_file_button = tk.Button(output_frame, text="Browse", command=browse_output_file, bg="#4CAF50", fg="white", font=("Helvetica", 10))
    output_file_button.pack(side=tk.LEFT, padx=5, pady=5)
    output_file_button.bind("<Enter>", on_enter)
    output_file_button.bind("<Leave>", on_leave)

    start_button = tk.Button(window, text="Start Processing", command=start_processing, bg="#4CAF50", fg="Black", font=("Helvetica", 12))
    start_button.place(relx=0.5, rely=0.7, anchor="center")
    start_button.bind("<Enter>", on_enter)
    start_button.bind("<Leave>", on_leave)

    status_label = tk.Label(window, text="", fg="black", bg="#004578", font=("Helvetica", 12))
    status_label.place(relx=0.5, rely=0.85, anchor="center")

   
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    x_coordinate = (screen_width / 2) - (window_width / 2)
    y_coordinate = (screen_height / 2) - (window_height / 2)
    window.geometry("+%d+%d" % (x_coordinate, y_coordinate))

    window.bind("<Configure>", on_resize)

    window.mainloop()

if __name__ == "__main__":
    run_script_with_gui()
