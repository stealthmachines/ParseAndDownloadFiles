import tkinter as tk
from tkinter import ttk  # Import ttk for Progressbar
from tkinter import messagebox
import threading
import requests
import os
from urllib.parse import urlparse

# Set the maximum number of simultaneous downloads
MAX_THREADS = 3
OUTPUT_DIR = "media"

# Create media folder if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def download_file(url, output_path, progress_var):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, stream=True, headers=headers)  # Add headers here
        response.raise_for_status()  # Will raise an exception for HTTP errors
        total_size = int(response.headers.get('content-length', 0))
        with open(output_path, 'wb') as file:
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    progress = (downloaded_size / total_size) * 100
                    progress_var.set(progress)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

def start_download_thread(url, output_dir, max_threads, progress_var):
    urlparse(url)
    # Example of parsing logic based on URL format
    file_name = url.split('/')[-1]
    output_path = os.path.join(output_dir, file_name)
    download_thread = threading.Thread(target=download_file, args=(url, output_path, progress_var))
    download_thread.start()

# GUI Setup
def create_gui():
    root = tk.Tk()
    root.title("Media Downloader")

    # URL Entry
    tk.Label(root, text="Enter URL:").pack(pady=10)
    url_entry = tk.Entry(root, width=50)
    url_entry.pack(pady=10)

    # Simultaneous Downloads Control
    tk.Label(root, text="Max simultaneous downloads:").pack(pady=5)
    max_threads_var = tk.IntVar(value=MAX_THREADS)
    max_threads_entry = tk.Entry(root, textvariable=max_threads_var, width=5)
    max_threads_entry.pack(pady=5)

    # Progress Bar
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(pady=20)

    # Buttons
    def start_download():
        url = url_entry.get().strip()
        max_threads = max_threads_var.get()
        if url:
            start_download_thread(url, OUTPUT_DIR, max_threads, progress_var)
        else:
            messagebox.showwarning("Invalid URL", "Please enter a valid URL.")
    
    start_button = tk.Button(root, text="Start Download", command=start_download)
    start_button.pack(pady=10)

    # Start the GUI loop
    root.mainloop()

# Run the GUI
if __name__ == "__main__":
    create_gui()
