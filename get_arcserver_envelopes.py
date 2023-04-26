import urllib3
import pandas as pd
import geopandas as gpd
import requests
import json
from shapely.geometry import Polygon
from json.decoder import JSONDecodeError
from pyproj import CRS
from pyproj.exceptions import CRSError

# Disable SSL warnings (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read the CSV file into a DataFrame

services = pd.read_csv("Parcel Scrape 04_23 Results.csv")

# Initialize an empty GeoDataFrame with the required columns
extents = gpd.GeoDataFrame(columns=["name", "full_link", "source", "geometry"])

# Initialize counters for successful and unsuccessful requests
successful_requests = 0
unsuccessful_requests = 0

for index, row in services.iterrows():
    # Make a request to the base URL with the parameter f=pjson
    try:
        response = requests.get(row['full_link'], params={"f": "json"}, verify=False, timeout=60)
    except requests.exceptions.Timeout as e:
        print(f"Timeout error for {row['full_link']} (Layer: {row['name']}): {e}")
        unsuccessful_requests += 1
        continue
    except requests.exceptions.RequestException as e:
        print(f"Connection error for {row['full_link']} (Layer: {row['name']}): {e}")
        unsuccessful_requests += 1
        continue

    if response.status_code == 200:
        try:
            data = json.loads(response.text)

            if "geometryType" in data and data["geometryType"] == "esriGeometryPolygon":
              
                wkid = None  # Initialize wkid variable

                if 'extent' in data:
                    # Extract the wkid, latestWkid or wkt from the JSON response
                    spatial_ref = data['extent']['spatialReference']
                    if 'latestWkid' in spatial_ref:
                        wkid = spatial_ref['latestWkid']
                    elif 'wkid' in spatial_ref:
                        wkid = spatial_ref['wkid']
                    elif 'wkt' in spatial_ref:
                        wkid = spatial_ref['wkt']
                    else:
                        print(f"No latestWkid, wkid, or wkt found for {row['full_link']} (Layer: {row['name']}). Skipping.")
                        unsuccessful_requests += 1
                        continue

                    if 'bbox' in data['extent']:
                        bbox = data['extent']['bbox']
                    elif all(key in data['extent'] for key in ['xmin', 'ymin', 'xmax', 'ymax']):
                        xmin = data['extent']['xmin']
                        ymin = data['extent']['ymin']
                        xmax = data['extent']['xmax']
                        ymax = data['extent']['ymax']
                        bbox = [xmin, ymin, xmax, ymax]
                    else:
                        print(f"No bounding box found for {row['full_link']}")
                        unsuccessful_requests += 1
                        continue
                # If the extent key is not available, make a request to the 'query' endpoint
                else:
                    query_url = row['full_link'] + "/query"
                    query_payload = {
                        "where": "1=1",
                        "geometryType": "esriGeometryPolygon",
                        "returnGeometry": "true",
                        "returnTrueCurves": "false",
                        "returnIdsOnly": "false",
                        "returnCountOnly": "false",
                        "returnExtentOnly": "true",
                        "f": "geojson",
                    }

                    try:
                        query_response = requests.get(query_url, params=query_payload, verify=False)
                    except requests.exceptions.RequestException as e:
                        print(f"Connection error for {query_url} (Layer: {row['name']}): {e}")
                        unsuccessful_requests += 1
                        continue

                    if query_response.status_code == 200:
                        try:
                            geojson_data = json.loads(query_response.text)

                            if 'error' in geojson_data:
                                print(f"Error in response for {row['full_link']}: {geojson_data['error']}")
                                unsuccessful_requests += 1
                                continue

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
                            else:
                                print(f"No bounding box found for {row['full_link']}")
                                unsuccessful_requests += 1
                                continue
                        except JSONDecodeError:
                            unsuccessful_requests += 1
                            print(f"Error decoding JSON for {query_url} (Layer: {row['name']}, status code: {query_response.status_code})")
                    else:
                        print(f"Error for {query_url} (Layer: {row['name']}, status code: {query_response.status_code})")
                        unsuccessful_requests += 1

                minx, miny, maxx, maxy = bbox

                # Create the bounding box polygon
                try:
                    bbox_polygon = Polygon([(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)])
                except Exception as e:
                    print(f"Error creating polygon for {row['full_link']} (Layer: {row['name']}): {e}")
                    unsuccessful_requests += 1
                    continue

                # Create the original CRS object
                if wkid is not None:
                    try:
                        original_crs = CRS.from_user_input(wkid)
                    except CRSError as e:
                        print(f"Error creating CRS for {row['full_link']} (Layer: {row['name']}): {e}")
                        # You can either skip the current iteration or set a default CRS
                        continue  # This will skip the current iteration
                else:
                    print(f"No wkid found for {row['full_link']} (Layer: {row['name']}). Skipping.")
                    unsuccessful_requests += 1
                    continue

                # Reproject the bounding box polygon to the WGS 84 format (EPSG:4326)
                bbox_gdf = gpd.GeoDataFrame({"geometry": [bbox_polygon]}, crs=original_crs)
                bbox_gdf_wgs84 = bbox_gdf.to_crs(epsg=4326)
                bbox_polygon_wgs84 = bbox_gdf_wgs84.geometry.iloc[0]

                # Append the bbox_polygon and the columns from the "services" DataFrame to the "extents" GeoDataFrame
                new_row = gpd.GeoDataFrame({
                    "name": [row["name"]],
                    "full_link": [row["full_link"]],
                    "source": [row["source"]],
                    "geometry": [bbox_polygon_wgs84]
                })
                extents = pd.concat([extents, new_row], ignore_index=True)

                successful_requests += 1
                print(f"Successfully requested {row['full_link']} (Layer: {row['name']})")
            else:
                print(f"Layer {row['name']} is not an esriGeometryPolygon")
                unsuccessful_requests += 1
        except JSONDecodeError:
            unsuccessful_requests += 1
            print(f"Error decoding JSON for {row['full_link']} (Layer: {row['name']}, status code: {response.status_code})")
    else:
        print(f"Error for {row['full_link']} (Layer: {row['name']}, status code: {response.status_code})")
        unsuccessful_requests += 1

    # At the end of the loop, print the request status
    print(f"Row {index + 1}:")
    print(f"  Successful requests: {successful_requests}")
    print(f"  Unsuccessful requests: {unsuccessful_requests}")
    print(f"  Total requests: {successful_requests + unsuccessful_requests}")

# Print the total number of successful and unsuccessful requests
print(f"\nTotal successful requests: {successful_requests}")
print(f"Total unsuccessful requests: {unsuccessful_requests}")

extents.to_file("extents.geojson", driver="GeoJSON")