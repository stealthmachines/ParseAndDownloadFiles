import os
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Constants
OUTPUT_DIR = "./media"
LOG_FILE = "./log.txt"

def fetch_url_content(url):
    """Fetch content from a URL with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*;q=0.8'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content

def parse_html(content):
    """Extract media links and metadata from HTML."""
    soup = BeautifulSoup(content, 'html.parser')
    links = []

    # Find all anchors pointing to media
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith(('.mp3', '.mp4', '.avi', '.mkv')):
            links.append({
                'url': href,
                'title': link.text.strip() or os.path.basename(href)
            })
    return links

def parse_xml(content):
    """Extract media links and metadata from XML."""
    tree = ET.fromstring(content)
    namespace = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

    items = []
    for item in tree.findall('channel/item'):
        title = item.findtext('title', '')
        enclosure = item.find('enclosure')
        if enclosure is not None:
            url = enclosure.get('url', '')
            items.append({
                'url': url,
                'title': title.strip(),
                'description': item.findtext('description', ''),
                'pubDate': item.findtext('pubDate', ''),
            })
    return items

def download_media(media, output_dir):
    """Download media files and save to the specified directory."""
    os.makedirs(output_dir, exist_ok=True)
    for item in media:
        url = item['url']
        title = item['title']
        file_name = os.path.join(output_dir, f"{title}.mp3" if '.mp3' in url else os.path.basename(url))
        
        print(f"Downloading {title} from {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved: {file_name}")

def main(url):
    """Main function to handle both HTML and XML sources."""
    content = fetch_url_content(url)
    parsed_url = urlparse(url)

    if url.endswith('.xml'):
        print("Detected XML feed...")
        media = parse_xml(content)
    else:
        print("Detected HTML page...")
        media = parse_html(content)

    # Create output directory based on the host
    host_dir = os.path.join(OUTPUT_DIR, parsed_url.netloc)
    download_media(media, host_dir)

    # Log results
    with open(LOG_FILE, 'a') as log:
        for item in media:
            log.write(f"{item['title']} - {item['url']}\n")
    print(f"Log updated: {LOG_FILE}")

if __name__ == "__main__":
    url = input("Enter URL to scrape (HTML or XML): ").strip()
    main(url)
