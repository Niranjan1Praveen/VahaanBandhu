import os
import requests
from flask import Flask
import folium
from supabase import create_client
from math import radians, cos, sin, sqrt, atan2
from dotenv import load_dotenv
import time

load_dotenv()
app = Flask(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Haversine formula to calculate distance in km between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_tomtom_route(start_lat, start_lon, end_lat, end_lon, api_key):
    """Get route geometry from TomTom Routing API"""
    url = (
        f"https://api.tomtom.com/routing/1/calculateRoute/"
        f"{start_lat},{start_lon}:{end_lat},{end_lon}/json?"
        f"routeType=fastest&traffic=true&travelMode=car&key={api_key}"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('routes'):
            print("No routes found in response")
            return []
        
        # Extract route points
        route_points = []
        for leg in data['routes'][0]['legs']:
            for point in leg['points']:
                route_points.append((point['latitude'], point['longitude']))
        return route_points
    except Exception as e:
        print(f"Routing API error: {str(e)}")
        return []

def get_traffic_color(lat, lon, api_key):
    """Get traffic color for a specific point using Traffic Flow API"""
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?point={lat},{lon}&unit=KMPH&key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Traffic API error: {response.status_code}")
            return 'gray'
        
        data = response.json()
        segment = data.get('flowSegmentData', {})
        current_speed = segment.get('currentSpeed', 0)
        free_flow_speed = segment.get('freeFlowSpeed', 0)
        
        if free_flow_speed <= 0 or current_speed <= 0:
            return 'gray'
        
        ratio = current_speed / free_flow_speed
        if ratio >= 0.9:
            return 'green'
        elif ratio >= 0.6:
            return 'orange'
        else:
            return 'red'
    except Exception as e:
        print(f"Traffic API exception: {str(e)}")
        return 'gray'

@app.route("/")
def map_view():
    # Initialize map with default center (India)
    map_center = [20.5937, 78.9629]
    zoom_level = 5
    api_key = "t97TBub7Ss9APxCbTxR6LXfCQtRb6JsB"  # Directly use provided API key

    # Get latest user location
    voice_responses = supabase.table("VoiceResponse").select("*").order("createdAt", desc=True).limit(1).execute().data or []
    current_user_lat = current_user_lon = None

    if voice_responses:
        current_user = voice_responses[0]
        current_user_lat = current_user.get("Latitude")
        current_user_lon = current_user.get("Longitude")

        if current_user_lat is not None and current_user_lon is not None:
            map_center = [current_user_lat, current_user_lon]
            zoom_level = 12

    m = folium.Map(location=map_center, zoom_start=zoom_level)

    # Add user marker
    if current_user_lat is not None and current_user_lon is not None:
        folium.Marker(
            location=[current_user_lat, current_user_lon],
            popup="\U0001F464 User (Latest Location)",
            icon=folium.Icon(color="blue", icon="user", prefix="fa")
        ).add_to(m)

    # Get all trucks
    trucks = supabase.table("Truck").select("*").execute().data or []
    nearest_truck = None
    min_distance = float("inf")
    distance_km = time_minutes = None

    # Find nearest truck
    if current_user_lat is not None and current_user_lon is not None:
        for truck in trucks:
            lat = truck.get("Latitude")
            lon = truck.get("Longitude")
            if lat is None or lon is None:
                continue
                
            distance = haversine(current_user_lat, current_user_lon, lat, lon)
            if distance < min_distance:
                min_distance = distance
                nearest_truck = truck
                nearest_truck_lat = lat
                nearest_truck_lon = lon

        # Calculate ETA if nearest truck found
        if nearest_truck:
            distance_km = min_distance
            truck_speed_kmh = 40  # Average truck speed
            time_minutes = (distance_km / truck_speed_kmh) * 60

    # Plot trucks
    for truck in trucks:
        lat = truck.get("Latitude")
        lon = truck.get("Longitude")
        name = truck.get("TruckDriverName", "Unnamed Truck")
        if lat is None or lon is None:
            continue

        is_nearest = nearest_truck and truck.get("id") == nearest_truck.get("id")
        color = "red" if is_nearest else "green"
        icon = "star" if is_nearest else "truck"

        folium.Marker(
            location=[lat, lon],
            popup=f"\U0001F69B {'🚩 Nearest: ' if is_nearest else ''}{name}",
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)


    # Generate route with traffic data
    if (nearest_truck and current_user_lat and current_user_lon and 
        nearest_truck_lat and nearest_truck_lon):
        
        route_points = get_tomtom_route(
            nearest_truck_lat, nearest_truck_lon,
            current_user_lat, current_user_lon,
            api_key
        )

        if route_points:
            # Draw base route
            folium.PolyLine(
                route_points,
                color='#555555',
                weight=6,
                opacity=0.5
            ).add_to(m)

            # Add traffic-colored segments with actual Traffic Flow API calls
            segment_size = 5  # Check traffic every N points
            colored_segments = []
            current_segment = []

            for i, (lat, lon) in enumerate(route_points):
                # Only check traffic every N points to reduce API calls
                if i % segment_size == 0:
                    # Get traffic color for this point using Traffic Flow API
                    color = get_traffic_color(lat, lon, api_key)
                    # If color changes or first point, start new segment
                    if colored_segments and colored_segments[-1][0] != color:
                        if current_segment:
                            colored_segments.append((color, current_segment))
                        current_segment = [(lat, lon)]
                    else:
                        current_segment.append((lat, lon))
                    # Add to segments if color changed
                    if not colored_segments:
                        colored_segments.append((color, current_segment))
                    elif colored_segments[-1][0] != color:
                        colored_segments.append((color, current_segment))
                        current_segment = [(lat, lon)]
                    # Add small delay to avoid rate limiting
                    time.sleep(0.1)
                else:
                    current_segment.append((lat, lon))

            # Add the last segment
            if current_segment:
                if colored_segments and colored_segments[-1][0] == color:
                    colored_segments[-1][1].extend(current_segment)
                else:
                    colored_segments.append((color, current_segment))

            # Draw colored segments on map
            for color, segment in colored_segments:
                if len(segment) > 1:
                    folium.PolyLine(
                        segment,
                        color=color,
                        weight=4,
                        opacity=0.9
                    ).add_to(m)

    # Add info legend
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 10px;
        z-index: 1000;
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
        font-size: 14px;
    ">
        <b>Traffic Guide</b><br>
        <span style="color:green;">▉</span> Good traffic (>90% speed)<br>
        <span style="color:orange;">▉</span> Moderate traffic (60-90%)<br>
        <span style="color:red;">▉</span> Heavy traffic (<60%)<br>
        <span style="color:grey;">▉</span> No data<br>
        <hr style="margin:5px 0">
        <b>Nearest Truck</b>: {truck_info}
    </div>
    """.format(
        truck_info=f"{distance_km:.2f} km, ETA: {time_minutes:.0f} min" 
        if distance_km and time_minutes else "Not available"
    )
    
    m.get_root().html.add_child(folium.Element(legend_html))
    return m._repr_html_()

if __name__ == "__main__":
    app.run(debug=True, port=5000)