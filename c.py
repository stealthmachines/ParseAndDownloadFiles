import requests
from bs4 import BeautifulSoup
import os

# URL of the page containing the list
url = "http://www.cuttingthroughthematrix.com/AlanWattPodCast.xml"  # Replace with the correct URL if different.

# Directory to save the downloaded files
download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# Set headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# Fetch the page
response = requests.get(url, headers=headers)
response.raise_for_status()

# Parse the page
soup = BeautifulSoup(response.text, 'html.parser')

# Find all <a> tags pointing to .mp3 files
links = soup.find_all('a', href=True)
mp3_links = [link for link in links if link['href'].endswith('.mp3')]

# Deduplicate links by href
unique_links = {}
for link in mp3_links:
    if link['href'] not in unique_links:
        unique_links[link['href']] = link.get_text(strip=True)

# Process each unique MP3 link
for href, label in unique_links.items():
    try:
        # Get descriptive text from adjacent links
        description = []
        for sibling in soup.find_all('a', href=href):
            description.append(sibling.get_text(strip=True))

        # Create a meaningful filename
        file_name = f"{' - '.join(description)}.mp3".replace('/', '_')
        file_path = os.path.join(download_dir, file_name)

        # Download the file
        print(f"Downloading {file_name} from {href}...")
        file_response = requests.get(href, headers=headers, stream=True)
        with open(file_path, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Saved to {file_path}.")

    except Exception as e:
        # Print the error and skip to the next file
        print(f"Error processing file {href}: {e}")
        continue

print("All files downloaded (skipped errors).")
