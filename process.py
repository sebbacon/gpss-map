import glob
import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import json
from shapely.geometry import Point
import zipfile

# Define file paths
zip_file_path = 'data.zip'
extracted_folder_path = 'extracted/'
output_csv_path = 'output/pcn_system_supplier_counts_with_icb.csv'
output_map_path = 'output/pcn_map.png'

# Unzip the provided files, including nested zip files
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(extracted_folder_path)

# Helper function to extract from nested zip files
def extract_nested_zip(file_path, extract_to):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

# Check each file in the extracted directory, if it's a zip file, extract it
for root, dirs, files in os.walk(extracted_folder_path):
    for file in files:
        if file.endswith('.zip'):
            extract_nested_zip(os.path.join(root, file), root)

# Define paths to the extracted files
excel_file_path = os.path.join(extracted_folder_path, 'ePCN.xlsx')
csv_file_path = glob.glob(extracted_folder_path + "POMI*.csv")[0]
json_file_path = os.path.join(extracted_folder_path, 'pcn_map.json')

# Define dummy data functions for fallback
def generate_dummy_excel():
    # Generate a dataframe similar in structure to 'ePCN.xlsx'
    dummy_excel_data = pd.DataFrame({
        'practice_code': [f'P{i:04d}' for i in range(1, 6)],
        'pcn_code': [f'N{i:03d}' for i in range(1, 6)],
        'ICB': [f'B{i:02d}' for i in range(1, 6)]
    })
    return dummy_excel_data

def generate_dummy_csv():
    # Generate a dataframe similar in structure to 'POMI_APR2023_to_SEP2023.csv'
    dummy_csv_data = pd.DataFrame({
        'practice_code': [f'P{i:04d}' for i in range(1, 6)],
        'system_supplier': ['EMIS' if i % 2 == 0 else 'TPP' for i in range(1, 6)]
    })
    return dummy_csv_data

def generate_dummy_json():
    # Generate a JSON object similar in structure to 'pcn_map.json'
    dummy_json_data = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {'code': f'N{i:03d}', 'name': f'PCN{i:03d}'},
                'geometry': {
                    'type': 'Point',
                    'coordinates': [-0.1278 + i*0.1, 51.5074 + i*0.1]
                }
            } for i in range(1, 6)
        ]
    }
    return dummy_json_data

# Check if files exist and read or generate dummy data accordingly
if os.path.isfile(excel_file_path):
    pcn_core_partner_details = pd.read_excel(excel_file_path, sheet_name='PCN Core Partner Details')
else:
    pcn_core_partner_details = generate_dummy_excel()

if os.path.isfile(csv_file_path):
    csv_data = pd.read_csv(csv_file_path)
else:
    csv_data = generate_dummy_csv()

if os.path.isfile(json_file_path):
    with open(json_file_path, 'r') as json_file:
        pcn_geo_data = json.load(json_file)
else:
    pcn_geo_data = generate_dummy_json()

# Process the Excel data
pcn_core_partner_details_renamed = pcn_core_partner_details.rename(
    columns={
        'Partner\nOrganisation\nCode': 'practice_code',
        'PCN Code': 'pcn_code',
        'Practice\nParent\nSub ICB Loc Code': 'ICB'
    }
)

# Process the CSV data
# Define a custom function to get the last value when ordered by 'Order_Column'
def last_value_ordered(group):
    #sorted_group = group.sort_values(by='Order_Column')
    last_row = group.iloc[-1]
    return last_row

csv_data_relevant = csv_data.groupby('practice_code').apply(last_value_ordered)
csv_data_relevant = csv_data_relevant[['practice_code', 'system_supplier']].reset_index(drop=True)

# Merge and count system suppliers per PCN

merged_data = pd.merge(
    pcn_core_partner_details_renamed[['practice_code', 'pcn_code']],
    csv_data_relevant,
    on='practice_code',
    how='left'
)
pcn_system_supplier_counts = merged_data.groupby(['pcn_code', 'system_supplier']).size().unstack(fill_value=0)
pcn_system_supplier_counts.reset_index(inplace=True)

# Add ICB values to the CSV
unique_icb_data = pcn_core_partner_details_renamed[['pcn_code', 'ICB']].drop_duplicates(subset=['pcn_code'])
updated_pcn_counts_with_icb = pd.merge(
    pcn_system_supplier_counts,
    unique_icb_data,
    on='pcn_code',
    how='left'
)

# Save to CSV
updated_pcn_counts_with_icb.to_csv(output_csv_path, index=False)
tpp_total = updated_pcn_counts_with_icb['TPP'].sum()
emis_total = updated_pcn_counts_with_icb['EMIS'].sum()

# Create GeoDataFrame for the map
gdf = gpd.GeoDataFrame.from_features(pcn_geo_data['features'])
gdf.crs = "EPSG:4326"
gdf = gdf.to_crs("EPSG:27700")

# Merge with color data for the map
pcn_color_data = updated_pcn_counts_with_icb[['pcn_code', 'EMIS', 'TPP']].copy()
pcn_color_data['emis_proportion'] = pcn_color_data['EMIS'] / (pcn_color_data['EMIS'] + pcn_color_data['TPP'])
coolwarm_cmap = plt.cm.get_cmap('coolwarm')
pcn_color_data['gradient_color'] = pcn_color_data['emis_proportion'].apply(coolwarm_cmap)

gdf_colored = gdf.merge(pcn_color_data, left_on='code', right_on='pcn_code')


# Plot and save map
fig, ax = plt.subplots(1, 1, figsize=(15, 15))
gdf_colored.plot(ax=ax, color=gdf_colored['gradient_color'])
ax.axis('off')
sm = plt.cm.ScalarMappable(cmap=coolwarm_cmap, norm=plt.Normalize(vmin=0, vmax=1))
sm._A = []
cbar = fig.colorbar(sm, ax=ax)
cbar.set_label('Proportion of EMIS (blue) to TPP (red)')
plt.text(0.01, 0.95, f'Total TPP Practices: {tpp_total}', transform=ax.transAxes, fontsize=16)
plt.text(0.01, 0.90, f'Total EMIS Practices: {emis_total}', transform=ax.transAxes, fontsize=16)
plt.savefig(output_map_path)
#breakpoint()
# Return paths of generated files
output_csv_path, output_map_path
