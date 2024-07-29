import geopandas as gpd
import googlemaps
import itertools
import requests
import base64
import os

# OpenAI API Key (gpt-4o required due to the token limit)
gpt_key = 'GPT API'
# Google Maps API Key
gmaps_key = "GOOGLE MAPS API"
# Setting up the Google Maps
gmaps = googlemaps.Client(key=gmaps_key)

def extract_intersections_within_polygon(road_shapefile, polygon_shapefile):
    try:
        print("Loading road shapefile...")
        roads_gdf = gpd.read_file(road_shapefile)
        print(f"Road shapefile loaded successfully. Number of geometries: {len(roads_gdf)}")

        print("Loading polygon shapefile...")
        polygon_gdf = gpd.read_file(polygon_shapefile)
        print(f"Polygon shapefile loaded successfully. Number of geometries: {len(polygon_gdf)}")

        # Reproject both shapefiles to EPSG:4326
        print("Reprojecting road shapefile to EPSG:4326...")
        roads_gdf = roads_gdf.to_crs(epsg=4326)
        print("Reprojecting polygon shapefile to EPSG:4326...")
        polygon_gdf = polygon_gdf.to_crs(epsg=4326)
        print("Reprojection completed.")

        # Ensure the polygon shapefile contains one polygon
        if len(polygon_gdf) != 1:
            print("The polygon shapefile should contain exactly one polygon.")
            return []

        polygon = polygon_gdf.geometry.iloc[0]
        
        # Ensure the road geometries are lines
        roads_gdf = roads_gdf[roads_gdf.geometry.type == 'LineString']
        print(f"Filtered LineString geometries. Number of LineString geometries: {len(roads_gdf)}")

        # Filter the road lines that intersect with the polygon
        roads_gdf = roads_gdf[roads_gdf.intersects(polygon)]
        print(f"Filtered roads that intersect with the polygon. Number of intersecting roads: {len(roads_gdf)}")

        # Create an empty list to store the intersections
        intersections = []

        # Compare each line with every other line to find intersections within the polygon
        total_combinations = len(roads_gdf) * (len(roads_gdf) - 1) // 2
        print(f"Total number of line combinations to check: {total_combinations}")

        count = 0
        for line1, line2 in itertools.combinations(roads_gdf.geometry, 2):
            count += 1
            if count % 1000 == 0:
                print(f"Checked {count} / {total_combinations} combinations")

            if line1.intersects(line2):
                intersection = line1.intersection(line2)
                if intersection.geom_type == 'Point' and polygon.contains(intersection):
                    intersections.append(intersection)
                elif intersection.geom_type == 'MultiPoint':
                    for point in intersection.geoms:
                        if polygon.contains(point):
                            intersections.append(point)

        # Extract the coordinates of the intersections
        coordinates = [(point.y, point.x) for point in intersections]  # Latitude and Longitude
        print(f"Number of intersections found: {len(coordinates)}")

        return coordinates

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def save_intersections_to_txt(coordinates, output_file):
    try:
        print("Saving intersections to text file...")
        with open(output_file, 'w') as f:
            for lat, lon in coordinates:
                f.write(f"{lat}, {lon}\n")
        print(f"Intersections saved to {output_file}")
    except Exception as e:
        print(f"An error occurred while saving to file: {e}")

def process_locations_file(input_file, api_key, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    with open(input_file, 'r') as file:
        locations = file.readlines()
    
    for location in locations:
        location = location.strip()
        get_streetview_images(location, api_key, output_folder)

# Retrieving the streetview images
def get_streetview_images(location, api_key, output_folder):
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    headings = [0, 90, 180, 270]
    params = {
        'location': location,
        'size': '450x450',
        'pitch': '0',  # Up or down angle of the camera
        'fov': '90',  # Field of view
        'source': 'default',
        'key': api_key
    }
    
    for heading in headings:
        params['heading'] = heading
        url = f"{base_url}?location={params['location']}&size={params['size']}&heading={params['heading']}&pitch={params['pitch']}&fov={params['fov']}&source={params['source']}&key={params['key']}"
        
        response = requests.get(url)
        if response.status_code == 200:
            image_filename = os.path.join(output_folder, f"{location.replace(',', '_')}_{heading}.jpg")
            with open(image_filename, 'wb') as file:
                file.write(response.content)
            print(f"Saved image: {image_filename}")
            if len(image_paths) < 250:
                image_paths.append(image_filename)
        else:
            print(f"Error for location {location} and heading {heading}: {response.status_code}, {response.text}")

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_images_with_gpt():
    encoded_images = [encode_image(image_path) for image_path in image_paths]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gpt_key}"
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here is a streetview photo of a region, analyse its walkability score out of 100 entirely based on the pedestrian experience while walking around the region. Another thing you should consider is accessibility around the region. There is a Canadian ADA Law for accessibility for disabled individuals (The Accessible Canada Act); use this as your references and reflect this aspect to your overall walkability score. At the very end, just provide the final score out of 100."
                }
            ]
        }
    ]

    for encoded_image in encoded_images:
        messages[0]['content'].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{encoded_image}"
            }
        })

    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 4096
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    res_json = response.json()
    
    print(res_json)

    # Extract and print the content
    if 'choices' in res_json:
        for choice in res_json['choices']:
            if 'message' in choice and 'content' in choice['message']:
                print(choice['message']['content'])
    else:
        print("No content available in the response.")

# Paths to your shapefiles
road_shapefile_path = '/Users/jangjaehyeong0421/VSC/Canurb/Google/mainstreet_base/msn_base.shp'
polygon_shapefile_path = '/Users/jangjaehyeong0421/VSC/Canurb/Google/bia/DowntownYonge/DTY.shp'
# Output file path
output_file_path = 'intersections.txt'

# Extract intersections within the polygon
print("Starting intersection extraction...")
intersections = extract_intersections_within_polygon(road_shapefile_path, polygon_shapefile_path)

# Save intersections to a text file
if intersections:
    save_intersections_to_txt(intersections, output_file_path)
else:
    print("No intersections found within the polygon.")

image_paths = []
output_folder = 'streetview_images'

process_locations_file(output_file_path, gmaps_key, output_folder)
analyze_images_with_gpt()
