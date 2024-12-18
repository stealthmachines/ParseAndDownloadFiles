import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# Constants
OUTPUT_DIR = "./media"
LOG_FILE = "./log.txt"

# Custom headers to bypass server restrictions
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

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

def download_media(media, output_dir):
    """Download media files and save to the specified directory."""
    os.makedirs(output_dir, exist_ok=True)
    for item in media:
        url = item['url']
        title = item['title']
        file_name = os.path.join(output_dir, f"{title}.mp3" if '.mp3' in url else os.path.basename(url))
        
        print(f"Downloading: {title}\nURL: {url}\nSaving to: {file_name}")
        try:
            response = requests.get(url, stream=True, headers=HEADERS)
            response.raise_for_status()
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
            print(f"Download successful: {file_name}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")
        except Exception as e:
            print(f"General error: {e}")

def main(url):
    """Main function to handle XML sources and download media."""
    try:
        content = fetch_url_content(url)
        media = parse_xml(content)

        # Create output directory based on the host
        parsed_url = urlparse(url)
        host_dir = os.path.join(OUTPUT_DIR, parsed_url.netloc)
        download_media(media, host_dir)

        # Log results
        with open(LOG_FILE, 'a') as log:
            for item in media:
                log.write(f"{item['title']} - {item['url']}\n")
        print(f"Log updated: {LOG_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    url = input("Enter URL to scrape (XML feed): ").strip()
    main(url)
