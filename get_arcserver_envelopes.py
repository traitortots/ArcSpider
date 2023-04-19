import pandas as pd
import requests
import geopandas as gpd
import urllib3
import json
from json.decoder import JSONDecodeError
from shapely.geometry import Polygon

# Disable SSL warnings (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read the CSV file into a DataFrame

services = pd.read_csv("Parcel Scrape 04_23 Results.csv")

# Query parameters
params = {
    "where": "1=1",
    "returnGeometry": "true",
    "returnTrueCurves": "false",
    "returnIdsOnly": "false",
    "returnCountOnly": "false",
    "returnExtentOnly": "true",
    "f": "geojson",
}

# Initialize an empty GeoDataFrame with the required columns
extents = gpd.GeoDataFrame(columns=["name", "full_link", "source", "geometry"])

# Initialize counters for successful and unsuccessful requests
successful_requests = 0
unsuccessful_requests = 0

for index, row in services.iterrows():
    # Append "/query" to the URL
    url = row['full_link'] + "/query"

    # Add necessary parameters for the API request
    payload = {
        "where": "1=1",
        "returnGeometry": "true",
        "returnTrueCurves": "false",
        "returnIdsOnly": "false",
        "returnCountOnly": "false",
        "returnExtentOnly": "true",
        "f": "geojson",
    }

    try:
        # Make the API request
        response = requests.get(url, params=payload, verify=False)
    except requests.exceptions.RequestException as e:
        print(f"Connection error for {url} (Layer: {row['name']}): {e}")
        unsuccessful_requests += 1
        continue

    if response.status_code == 200:
        try:
            # Load the GeoJSON response into a Python dictionary
            geojson_data = json.loads(response.text)

            if 'error' in geojson_data:
                print(f"Error in response for {row['full_link']}: {geojson_data['error']}")
                unsuccessful_requests += 1
                continue

            # Extract the bounding box coordinates
            if 'extent' in geojson_data:
                if 'bbox' in geojson_data['extent']:
                    bbox = geojson_data['extent']['bbox']
                elif all(key in geojson_data['extent'] for key in ['xmin', 'ymin', 'xmax', 'ymax']):
                    xmin = geojson_data['extent']['xmin']
                    ymin = geojson_data['extent']['ymin']
                    xmax = geojson_data['extent']['xmax']
                    ymax = geojson_data['extent']['ymax']
                    bbox = [xmin, ymin, xmax, ymax]
                else:
                    print(f"No bounding box found for {row['full_link']}")
                    unsuccessful_requests += 1
                    continue
            elif 'bbox' in geojson_data:
                bbox = geojson_data['bbox']
            else:
                print(f"No bounding box found for {row['full_link']}")
                unsuccessful_requests += 1
                continue

            minx, miny, maxx, maxy = bbox

            # Create the bounding box polygon
            try:
                bbox_polygon = Polygon([(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)])
            except Exception as e:
                print(f"Error creating polygon for {row['full_link']} (Layer: {row['name']}): {e}")
                unsuccessful_requests += 1
                continue

            # Append the bbox_polygon and the columns from the "services" DataFrame to the "extents" GeoDataFrame
            new_row = gpd.GeoDataFrame({
                "name": [row["name"]],
                "full_link": [row["full_link"]],
                "source": [row["source"]],
                "geometry": [bbox_polygon]
            })
            extents = pd.concat([extents, new_row], ignore_index=True)

            successful_requests += 1
            print(f"Successfully requested {row['full_link']} (Layer: {row['name']})")
        except JSONDecodeError:
            unsuccessful_requests += 1
            print(f"Error decoding JSON for {url} (Layer: {row['name']}, status code: {response.status_code})")
    else:
        print(f"Error for {url} (Layer: {row['name']}, status code: {response.status_code})")
        unsuccessful_requests += 1

    print(f"Successful requests: {successful_requests}, Unsuccessful requests: {unsuccessful_requests}, Total requests: {successful_requests + unsuccessful_requests}")

extents.to_file("extents.geojson", driver="GeoJSON")