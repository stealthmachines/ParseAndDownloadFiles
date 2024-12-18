import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import tkinter as tk
from tkinter import ttk  # Import ttk for Progressbar

# Constants
OUTPUT_DIR = "./media"
LOG_FILE = "./log.txt"
MAX_RETRIES = 3
MAX_THREADS = 4  # Optimal number of simultaneous downloads
DOWNLOAD_PROGRESS_FILE = "download_progress.json"

# Custom headers to bypass server restrictions
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to sanitize file names by removing or replacing invalid characters
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def fetch_url_content(url):
    """Fetch content from a URL with custom headers."""
    print(f"Fetching XML from: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.content

def parse_xml(content):
    """Extract media links and metadata from XML."""
    print("Parsing XML content...")
    tree = ET.fromstring(content)
    items = []
    for item in tree.findall('channel/item'):
        title = item.findtext('title', '').strip()
        enclosure = item.find('enclosure')
        if enclosure is not None:
            url = enclosure.get('url', '').strip()
            if url:
                items.append({
                    'url': url,
                    'title': title,
                })
    print(f"Found {len(items)} media files.")
    return items

def download_media_item(item, output_dir, retries=0):
    """Download a media file and save it to the specified directory."""
    url = item['url']
    title = item['title']
    sanitized_title = sanitize_filename(title)  # Sanitize the title to avoid invalid characters in the filename
    
    # Ensure the file path is safe for Windows
    file_name = os.path.join(output_dir, f"{sanitized_title}.mp3" if '.mp3' in url else os.path.basename(url))
    
    print(f"Downloading: {title}\nURL: {url}\nSaving to: {file_name}")
    
    attempt = 0
    success = False
    
    # Retry mechanism
    while attempt < MAX_RETRIES and not success:
        try:
            response = requests.get(url, stream=True, headers=HEADERS)
            response.raise_for_status()
            
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
            print(f"Download successful: {file_name}")
            success = True
        except requests.exceptions.RequestException as e:
            attempt += 1
            print(f"Error downloading {url}: {e}. Attempt {attempt}/{MAX_RETRIES}")
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            print(f"General error: {e}")
            break
    
    return success, item

def download_media(media, output_dir, max_threads, progress_var):
    """Download media files using parallel threads with progress tracking."""
    os.makedirs(output_dir, exist_ok=True)
    total_files = len(media)
    
    # Initialize progress tracking
    downloaded = 0
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(download_media_item, item, output_dir): item for item in media}
        
        for future in as_completed(futures):
            item = futures[future]
            success, item = future.result()
            if success:
                downloaded += 1
            progress_var.set(downloaded / total_files * 100)
            time.sleep(0.1)  # Small delay to prevent UI from freezing

def save_progress(media, filename=DOWNLOAD_PROGRESS_FILE):
    """Save download progress to a file."""
    progress = {"downloads": media}
    with open(filename, "w") as f:
        json.dump(progress, f)

def load_progress(filename=DOWNLOAD_PROGRESS_FILE):
    """Load download progress from a file."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f).get("downloads", [])
    return []

def start_download_thread(url, output_dir, max_threads, progress_var):
    """Start the download process in a separate thread."""
    def download_thread():
        try:
            content = fetch_url_content(url)
            media = parse_xml(content)

            # Create output directory based on the host
            parsed_url = urlparse(url)
            host_dir = os.path.join(output_dir, parsed_url.netloc)

            # Load previous progress (if available) and resume from where we left off
            progress = load_progress()
            remaining_media = [item for item in media if item not in progress]
            
            if remaining_media:
                download_media(remaining_media, host_dir, max_threads, progress_var)
                save_progress(media)  # Save progress after download completion
            else:
                print("All media files have already been downloaded.")
                messagebox.showinfo("Download Complete", "All files have already been downloaded.")
        except Exception as e:
            print(f"An error occurred: {e}")
            messagebox.showerror("Download Error", str(e))
    
    # Start the download in a new thread
    thread = Thread(target=download_thread)
    thread.daemon = True
    thread.start()

def stop_download():
    """Stop the download process."""
    # Handle stopping of download, perhaps by marking state or manually interrupting thread
    pass

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

if __name__ == "__main__":
    create_gui()
