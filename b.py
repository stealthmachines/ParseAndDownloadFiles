import requests
from bs4 import BeautifulSoup
import os

# URL of the page containing the list
url = "https://zchg.org/t/hour-of-the-time-bill-cooper/536"  # Replace with the correct URL if different.

# Directory to save the downloaded files
download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# Fetch the page
response = requests.get(url)
response.raise_for_status()

# Parse the page
soup = BeautifulSoup(response.text, 'html.parser')
rows = soup.select('table tr')  # Assuming the table structure in your example.

# Process each row and download files
for row in rows[1:]:  # Skip the header row
    try:
        columns = row.find_all('td')
        if len(columns) < 4:
            continue  # Skip malformed rows

        tape_number = columns[0].get_text(strip=True)
        file_link = columns[0].find('a')['href']  # This may throw an error
        title = columns[2].get_text(strip=True)

        # File name for saving
        file_name = f"{tape_number} - {title}.mp3".replace('/', '_')
        file_path = os.path.join(download_dir, file_name)

        # Download the file
        print(f"Downloading {file_name} from {file_link}...")
        file_response = requests.get(file_link, stream=True)
        with open(file_path, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Saved to {file_path}.")

    except Exception as e:
        # Print the error and skip to the next row
        print(f"Error processing row: {e}")
        continue

print("All files downloaded (skipped errors).")
