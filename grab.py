import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import zipfile
import os

# Function to download a file using streaming to handle large files
def download_file(url, filename):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
    print(f"Downloaded {filename}")

# Function to zip files
def zip_files(filenames, zip_name):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in filenames:
            zipf.write(file, arcname=os.path.basename(file))
    print(f"Created zip file {zip_name}")

# Step 1: Fetch the HTML content from NHS URL
nhs_url = "https://digital.nhs.uk/data-and-information/publications/statistical/mi-patient-online-pomi/current"
response = requests.get(nhs_url)
response.raise_for_status()

# Step 2: Parse the HTML for the first ZIP file with the specified class
soup = BeautifulSoup(response.text, 'html.parser')
zip_link = csv_link = None

for link in soup.find_all('a', class_='nhsd-a-box-link'):
    href = link.get('href', '')
    if href.endswith('.zip'):
        zip_link = href
        break
    elif href.endswith('.csv'):
        csv_link = href
        break

if not zip_link and not csv_link:
    raise ValueError("No zip or csv file found with the specified class.")

# Step 3: Download the NHS ZIP file
link = zip_link or csv_link
nhs_url = urljoin(nhs_url, link)
nhs_filename = nhs_url.split('/')[-1]
download_file(nhs_url, nhs_filename)

# Step 4: Download the ePCN ZIP file
epcn_url = "https://digital.nhs.uk/binaries/content/assets/website-assets/services/ods/data-downloads-other-nhs-organisations/epcn.zip"
epcn_filename = "ePCN.zip"
download_file(epcn_url, epcn_filename)

# Step 5: Download the JSON data from the OpenPrescribing API
pcn_api_url = "https://openprescribing.net/api/1.0/org_location/?org_type=pcn"
pcn_map_response = requests.get(pcn_api_url)
pcn_map_response.raise_for_status()
pcn_map_filename = "pcn_map.json"

# Save the JSON data
with open(pcn_map_filename, 'w') as file:
    file.write(pcn_map_response.text)
print("Downloaded pcn_map.json")

# Step 6: Zip all the downloaded files into data.zip
files_to_zip = [nhs_filename, epcn_filename, pcn_map_filename]
zip_files(files_to_zip, "data.zip")

# Optional: Clean up the original files after zipping if needed
# for file in files_to_zip:
#     os.remove(file)
# print("Cleaned up original files.")
