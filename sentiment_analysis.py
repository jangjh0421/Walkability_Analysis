import googlemaps
import requests
import json
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import itertools
import numpy as np

# Initialize a set to store sentiment scores
score_set = set()

#_______________________________________________
key = 'GOOGLE MAPS API KEY'
OPENAI_API_KEY = 'OPEN AI API KEY'

# Paths to your shapefiles
road_shapefile_path = 'PATH TO ROAD NETWORK FILES'
polygon_shapefile_path = 'PATH TO ONE POLYGON .SHP FILES'
#_______________________________________________

gmaps = googlemaps.Client(key=key)

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

def perform_nearby_search(coordinates, radius, polygon, place_ids_set):
    try:
        print("Performing Nearby Search...")

        for lat, lon in coordinates:
            params = {
                'location': f'{lat},{lon}',
                'radius': radius,  # Radius in meters
                'key': key
            }

            url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
            response = requests.get(url, params=params)

            if response.status_code == 200:
                places_result = response.json().get('results', [])
                for place in places_result:
                    place_location = place['geometry']['location']
                    place_point = Point(place_location['lng'], place_location['lat'])
                    if polygon.contains(place_point):
                        place_ids_set.add(place['place_id'])
            else:
                print(f"Error {response.status_code}: {response.text}")

        print(f"Number of unique Place IDs found within the polygon: {len(place_ids_set)}")

    except Exception as e:
        print(f"An error occurred during Nearby Search: {e}")

def process_review(reviews):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Here is a list of reviews about a specific place. \
                Perform a sentiment analysis on these reviews to determine the overall \
                sentiment towards the place. Provide a numeric measure out of 100, where 100 \
                indicates a highly positive sentiment and total satisfaction, and lower scores \
                indicate more negative experiences. You should only return one numeric measure. \
                Do not include any additional words or commentary—just the number. Here are the reviews:" + reviews
            }
        ],
        "max_tokens": 4096
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    result = response.json()
    description = result['choices'][0]['message']['content']
    return description

def perform_sentiment_analysis_on_place_ids(place_ids):
    try:
        sentiment_scores = []

        for place_id in place_ids:
            params = {
                'place_id': place_id,
                'fields': 'rating,reviews',
                'key': key
            }

            url = 'https://maps.googleapis.com/maps/api/place/details/json'
            response = requests.get(url, params=params)

            if response.status_code == 200:
                place_details = response.json().get('result', {})
                if 'reviews' in place_details:
                    reviews_texts = [review['text'] for review in place_details['reviews']]
                    reviews_combined = ' '.join(reviews_texts)
                    sentiment_analysis = process_review(reviews_combined)
                    sentiment_scores.append(int(sentiment_analysis))
                    score_set.add(int(sentiment_analysis))
                else:
                    print(f"Place ID: {place_id} has no reviews.")
            else:
                print(f"Error fetching details for Place ID: {place_id}, {response.status_code}: {response.text}")

        with open('sentiment_analysis_results.txt', 'w') as f:
            for place_id, sentiment_score in zip(place_ids, sentiment_scores):
                f.write(f"Place ID: {place_id}, Sentiment Score: {sentiment_score}\n")

        print("Sentiment analysis results saved to sentiment_analysis_results.txt")

        return sentiment_scores

    except Exception as e:
        print(f"An error occurred during sentiment analysis: {e}")

def calculate_five_number_summary(scores):
    min_score = np.min(scores)
    q1_score = np.percentile(scores, 25)
    median_score = np.median(scores)
    q3_score = np.percentile(scores, 75)
    max_score = np.max(scores)
    return min_score, q1_score, median_score, q3_score, max_score

# Output file path
intersections_file_path = 'intersections.txt'
places_file_path = 'places.txt'

# Radius for Nearby Search (in meters)
radius = 400

# Extract intersections within the polygon
print("Starting intersection extraction...")
intersections = extract_intersections_within_polygon(road_shapefile_path, polygon_shapefile_path)

# Save intersections to a text file
if intersections:
    save_intersections_to_txt(intersections, intersections_file_path)

    # Load the polygon shapefile again to get the polygon geometry
    polygon_gdf = gpd.read_file(polygon_shapefile_path)
    polygon_gdf = polygon_gdf.to_crs(epsg=4326)
    polygon = polygon_gdf.geometry.iloc[0]

    # Perform Nearby Search and save unique Place IDs to a set
    unique_place_ids = set()
    for intersection in intersections:
        perform_nearby_search([intersection], radius, polygon, unique_place_ids)

    # Convert the set to a list for processing
    unique_place_ids = list(unique_place_ids)

    # Perform sentiment analysis on the unique Place IDs
    sentiment_scores = perform_sentiment_analysis_on_place_ids(unique_place_ids)

    # Calculate and print the five-number summary
    if sentiment_scores:
        min_score, q1_score, median_score, q3_score, max_score = calculate_five_number_summary(sentiment_scores)
        print(f"Five Number Summary of Sentiment Scores:")
        print(f"Min: {min_score}")
        print(f"Q1: {q1_score}")
        print(f"Median: {median_score}")
        print(f"Q3: {q3_score}")
        print(f"Max: {max_score}")
else:
    print("No intersections found within the polygon.")
