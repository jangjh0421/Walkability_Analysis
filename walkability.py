import googlemaps
import os
import requests
import json
from datetime import datetime
from openai import OpenAI

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import itertools


#_______________________________________________
key = 'GOOGLE MAPS API KEY'
OPENAI_API_KEY = 'OPEN AI API KEY'

# Paths to your shapefiles
road_shapefile_path = 'PATH TO ROAD NETWORK FILES'
polygon_shapefile_path = 'PATH TO ONE POLYGON .SHP FILES'
#_______________________________________________

gmaps = googlemaps.Client(key=key) 
count = 0

def get_streetview_images(location, api_key, output_folder):
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    headings = [0, 90, 180, 270]
    params = {
        'location': location,
        'size': '1080x1080',
        'pitch': '0',  # Up or down angle of the camera
        'fov': '90',  # Field of view
        'source': 'default',  # Source of imagery
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
        else:
            print(f"Error for location {location} and heading {heading}: {response.status_code}, {response.text}")

def process_locations_file(input_file, api_key, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    with open(input_file, 'r') as file:
        locations = file.readlines()
    
    for location in locations:
        location = location.strip()
        get_streetview_images(location, api_key, output_folder)

def describe_image(filename):
    description = f"Description of the image {filename}: The image shows a street view. Analyze it comprehensively to identify the presence and conditions of pedestrian infrastructure, including sidewalks, crosswalks, pedestrian walk signals, ramps at curbs, and designated bike paths. Additionally, note any constructions, graffiti, road cracks, pavement conditions, road hygiene, overgrown grass around the sidewalk, and any other details that might affect walkability. Consider the following aspects: Presence and condition of pedestrian walk signals; Presence and accessibility of curb ramps; Visibility and condition of marked crosswalks; Type of land use (residential, commercial, mixed-use); Number and condition of public parks; Number and condition of public transit stops; Presence and condition of designated bike paths; Availability and condition of benches or places to sit; Installation and condition of streetlights; Maintenance status of buildings; Presence and visibility of graffiti/tagging; Presence and condition of sidewalks; Identification of poorly maintained sections of the sidewalk that pose trip hazards; Presence and condition of buffers between sidewalks and streets; Extent of overhead coverage by trees, awnings, or other structures. Your descriptive text should include all these details to facilitate a thorough micro-scale walkability analysis -- but please try to make every description concise and reasonably short!"

    return description

def analyze_images_with_gpt(folder):
    descriptions = []

    for filename in os.listdir(folder):
        if filename.endswith((".jpg", ".png")):
            description = describe_image(filename)
            descriptions.append(description)

    massive_prompt = "I will provide text descriptions of various images from Google Maps Street View. Please conduct a detailed, micro-level walkability analysis of the specified area. Pay close attention to factors such as construction sites, graffiti, road cracks, pavement conditions, cleanliness, overgrown grass near sidewalks, and other minor details that could affect the desirability of walking in the area. Additionally, consider the following standards in your analysis: Crossing: Is a pedestrian walk signal present? Is there a ramp at the curb(s)? Is there a marked crosswalk? Segment: Type of land use? How many public parks are present? How many public transit stops are present? Is there a designated bike path? Are there any benches or places to sit? Are streetlights installed? Are the buildings well maintained? Is graffiti/tagging present? Is a sidewalk present? Are there poorly maintained sections of the sidewalk that constitute major trip hazards? Is a buffer present? What percentage of the length of the sidewalk/walkway is covered by trees, awnings, or other overhead coverage? You don't need to analyze every single image individually; instead, summarize your findings in one comprehensive paragraph. Additionally, provide a walkability score out of 100, reflecting the overall pedestrian-friendliness of the area. Present the final output in the following format: Walkability Score: [numeric score] Explanations: - [Bullet point explanation 1] - [Bullet point explanation 2] - ... Please note: - If the area is pedestrian-friendly, with features like trees, minimal traffic, walkable shades, and a peaceful environment, the score should be very high (around 80-90). - A lack of trees and green spaces should result in a lower score. - Areas that do not appear to be major retail or residential zones should have a lower score. - A residential area with trees, fewer cars, and shaded walkways should have a very high score, around 90." + "\n\n".join(descriptions)

    client = OpenAI(
        api_key=OPENAI_API_KEY,
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
                {
                    "role": "user",
                    "content": massive_prompt,
                }
            ],
        max_tokens=4096
    )

    response_content = response.choices[0].message.content

    # Convert the response to JSON format
    walkability_score = response_content.split("Walkability Score: ")[1].split("\n")[0]
    explanations = response_content.split("Explanations:")[1].strip().split("\n- ")

    result = {
        "Walkability Score": int(walkability_score),
        "Explanations": explanations
    }

    return result


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
        count = 4 * len(coordinates)
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

api_key = key
output_folder = 'streetview_images'

process_locations_file(output_file_path, api_key, output_folder)
walkability_results = analyze_images_with_gpt(output_folder)

# Save the JSON result to a file named "report.json"
with open('report.json', 'w') as json_file:
    json.dump(walkability_results, json_file, indent=4)

print("Walkability results saved to report.json")
