import os
import requests
from flask import Flask
import folium
from folium.plugins import AntPath
from supabase import create_client
from math import radians, cos, sin, sqrt, atan2
from dotenv import load_dotenv
import time
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.providers.basic_provider import BasicSimulator
# app.py (top)
from Qdelay import quantum_delay_prediction

# Pretrained RX angles (radians) per qubit, from your offline training
PRETRAINED_THETAS = [0.2, -0.1, 0.3, 0.4, -0.2]

# Load environment variables
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

def quantum_route_evaluation(traffic_ratios):
    """Simple quantum circuit to evaluate route segments"""
    if not traffic_ratios or len(traffic_ratios) < 2:
        return []
    
    # Create a quantum circuit
    num_qubits = min(5, len(traffic_ratios))  # Limit to 5 qubits for simplicity
    qc = QuantumCircuit(num_qubits)
    
    # Encode traffic ratios as quantum states
    for i in range(num_qubits):
        if traffic_ratios[i] > 0.7:  # Good traffic
            qc.x(i)  # Flip to |1> state
    
    # Add entanglement to correlate good segments
    for i in range(num_qubits-1):
        qc.cx(i, i+1)
    
    # Measure all qubits
    qc.measure_all()
    
    # Run simulation
    simulator = BasicSimulator()
    compiled_circuit = transpile(qc, simulator)
    result = simulator.run(compiled_circuit).result()
    counts = result.get_counts(qc)
    
    # Get most frequent measurement
    best_path = max(counts, key=counts.get)
    
    # Convert to segment indices (1=good, 0=bad)
    return [i for i, val in enumerate(best_path[::-1]) if val == '1']

def adjust_marker_position(base_lat, base_lon, existing_positions, offset_deg=0.002):
    """Adjust marker position to avoid overlap with existing markers"""
    new_lat, new_lon = base_lat, base_lon
    
    # Try different offsets until we find a non-overlapping position
    for i in range(1, 5):
        for direction in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # E, N, W, S
            candidate_lat = base_lat + direction[0] * offset_deg * i
            candidate_lon = base_lon + direction[1] * offset_deg * i
            
            # Check if candidate is sufficiently far from existing markers
            too_close = False
            for existing_lat, existing_lon in existing_positions:
                if abs(candidate_lat - existing_lat) < offset_deg and abs(candidate_lon - existing_lon) < offset_deg:
                    too_close = True
                    break
            
            if not too_close:
                return candidate_lat, candidate_lon
    
    # If all offsets fail, return original position
    return base_lat, base_lon

@app.route("/")
def map_view():
    # Initialize map with default center (India)
    map_center = [20.5937, 78.9629]
    zoom_level = 5
    api_key = "UzMMAF8tgfNGRsjn35LDuPdyYajHgKsw"  # TomTom API key

    # Get latest user location
    voice_responses = supabase.table("VoiceResponse").select("*").order("createdAt", desc=True).limit(1).execute().data or []
    current_user_lat = current_user_lon = None
    current_user = None

    if voice_responses:
        current_user = voice_responses[0]
        current_user_lat = current_user.get("Latitude")
        current_user_lon = current_user.get("Longitude")

        if current_user_lat is not None and current_user_lon is not None:
            map_center = [current_user_lat, current_user_lon]
            zoom_level = 12

    m = folium.Map(location=map_center, zoom_start=zoom_level)
    
    # Track existing marker positions to prevent overlap
    existing_marker_positions = []

    # Add user marker
    if current_user_lat is not None and current_user_lon is not None:
        folium.Marker(
            location=[current_user_lat, current_user_lon],
            popup="\U0001F464 User (Latest Location)",
            icon=folium.Icon(color="blue", icon="user", prefix="fa")
        ).add_to(m)
        existing_marker_positions.append((current_user_lat, current_user_lon))

    # Get all trucks
    trucks = supabase.table("Truck").select("*").execute().data or []
    nearest_truck = None
    min_distance = float("inf")
    distance_km = time_minutes = None
    nearest_truck_lat = nearest_truck_lon = None
    nearest_truck_name = "Nearest Truck"
    mandi_lat = mandi_lon = None

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
                nearest_truck_name = truck.get("TruckDriverName", "Nearest Truck")

        # Calculate ETA if nearest truck found
        if nearest_truck:
            distance_km = min_distance
            truck_speed_kmh = 40  # Average truck speed
            time_minutes = (distance_km / truck_speed_kmh) * 60

    # --- Add Mandi (Market) Marker from VoiceResponse ---
    if current_user and current_user.get("market"):
        latest_market = current_user.get("market")
        cleaned_market = latest_market.strip().split()[0]
        mandi_entries = supabase.table("MandiLatLong")\
            .select("*")\
            .ilike("Mandi_Hindi", f"%{cleaned_market}%")\
            .execute().data

        if mandi_entries:
            mandi = mandi_entries[0]
            mandi_lat = mandi.get("Latitude")
            mandi_lon = mandi.get("Longitude")
            mandi_name = mandi.get("Mandi")
            mandi_name_hindi = mandi.get("Mandi_Hindi")
            mandi_state = mandi.get("State")

            if mandi_lat and mandi_lon:
                # Check if mandi is too close to existing markers
                mandi_display_lat, mandi_display_lon = adjust_marker_position(
                    mandi_lat, mandi_lon, existing_marker_positions
                )
                
                folium.Marker(
                    location=[mandi_display_lat, mandi_display_lon],
                    popup=f"Mandi: {mandi_name_hindi} ({mandi_name}, {mandi_state})",
                    icon=folium.Icon(color="orange", icon="shopping-cart", prefix="fa")
                ).add_to(m)
                existing_marker_positions.append((mandi_display_lat, mandi_display_lon))

    # Plot trucks and add moving animation
    if nearest_truck_lat and nearest_truck_lon:
        # Adjust truck position if it overlaps with mandi
        truck_display_lat, truck_display_lon = adjust_marker_position(
            nearest_truck_lat, nearest_truck_lon, existing_marker_positions
        )
        
        # Add special marker for nearest truck
        folium.Marker(
            location=[truck_display_lat, truck_display_lon],
            popup=(
                f"\U0001F69B Nearest Truck: {nearest_truck_name}<br>"
                f"Distance: {distance_km:.2f} km<br>"
                f"ETA: {time_minutes:.0f} min"
            ),
            icon=folium.Icon(color="red", icon="truck", prefix="fa"),
            tooltip="Nearest Truck (Starting Point)"
        ).add_to(m)
        existing_marker_positions.append((truck_display_lat, truck_display_lon))

        # Draw straight-line connection to user
        # if current_user_lat and current_user_lon:
        #     folium.PolyLine(
        #         locations=[[current_user_lat, current_user_lon], [truck_display_lat, truck_display_lon]],
        #         color="blue",
        #         weight=2.5,
        #         dash_array="5, 10",
        #         popup=f"Direct Distance: {distance_km:.2f} km"
        #     ).add_to(m)

    # Add regular markers for other trucks
    for truck in trucks:
        lat = truck.get("Latitude")
        lon = truck.get("Longitude")
        name = truck.get("TruckDriverName", "Unnamed Truck")
        if lat is None or lon is None:
            continue

        # Skip if this is the nearest truck (already added)
        if nearest_truck and truck.get("id") == nearest_truck.get("id"):
            continue
            
        # Adjust position to avoid overlap
        truck_display_lat, truck_display_lon = adjust_marker_position(lat, lon, existing_marker_positions)
        
        folium.Marker(
            location=[truck_display_lat, truck_display_lon],
            popup=f"\U0001F69B {name}",
            icon=folium.Icon(color="green", icon="truck", prefix="fa")
        ).add_to(m)
        existing_marker_positions.append((truck_display_lat, truck_display_lon))

    # Generate route with traffic data
    if (nearest_truck_lat and nearest_truck_lon and 
        current_user_lat and current_user_lon):
        
        # Route: Truck → User
        route1 = get_tomtom_route(
            nearest_truck_lat, nearest_truck_lon,
            current_user_lat, current_user_lon,
            api_key
        )

        # Create truck animation for route1
        if route1:
            # Add moving truck animation
            AntPath(
                locations=route1,
                color='blue',
                pulse_color='red',
                delay=1500,  # Animation speed (ms) - higher is slower
                dash_array=[10, 20],
                weight=5,
                opacity=0.7,
                icon='truck',
                icon_size=(30, 30),  # Icon size
                rotate=True,  # Rotate with path direction
                popup=f"Moving Truck: {nearest_truck_name}",
                tooltip="Truck moving to your location"
            ).add_to(m)
            
            # Collect traffic data for quantum evaluation
            traffic_ratios = []
            sample_points = []
            sample_rate = max(1, len(route1)) // 5  # Sample 5 points

            for i, (lat, lon) in enumerate(route1):
                if i % sample_rate == 0:
                    color = get_traffic_color(lat, lon, api_key)
                    ratio = 0.9 if color == 'green' else 0.6 if color == 'orange' else 0.3
                    traffic_ratios.append(ratio)
                    sample_points.append((lat, lon))
                    time.sleep(0.1)

            # Run quantum evaluation if we have enough points
            if len(traffic_ratios) >= 2:
                # 1) Predict delay in minutes via your QDelay module
                predicted_delay = quantum_delay_prediction(
                    traffic_ratios,
                    trained_thetas=PRETRAINED_THETAS,  # from your top‐of‐file import
                    max_delay=45.0                     # adjust as needed
                )

                # 2) Unpack the last sample point for accurate placement
                lat, lon = sample_points[-1]

                # 3) Render a small info‐card at that point
                card_html = f"""
                <div style="
                    padding:6px 10px;
                    font-family:Arial, sans-serif;
                    text-align:center;
                ">
                    <strong style="font-size:13px;">अनुमानित विलंब</strong><br>
                    <span style="font-size:15px; color:blue;">
                        ⏱ {predicted_delay:.1f} min
                    </span>
                </div>
                """

                folium.Marker(
                    location=[lat, lon],
                    icon=folium.DivIcon(html=card_html)
                ).add_to(m)

            # Add traffic-colored segments
            segment_size = 3  # Check traffic every N points
            colored_segments = []
            current_segment = []
            current_color = None

            for i, (lat, lon) in enumerate(route1):
                if i % segment_size == 0:
                    color = get_traffic_color(lat, lon, api_key)
                    if current_color is None:
                        current_color = color
                    
                    if color != current_color and current_segment:
                        colored_segments.append((current_color, current_segment))
                        current_segment = [(lat, lon)]
                        current_color = color
                    else:
                        current_segment.append((lat, lon))
                    time.sleep(0.1)
                else:
                    current_segment.append((lat, lon))

            if current_segment:
                colored_segments.append((current_color, current_segment))

            for color, segment in colored_segments:
                if len(segment) > 1:
                    folium.PolyLine(
                        segment,
                        color=color,
                        weight=4,
                        opacity=0.9
                    ).add_to(m)

    # Add route to Mandi if available
    if (mandi_lat and mandi_lon and 
        current_user_lat and current_user_lon):
        
        route2 = get_tomtom_route(
            current_user_lat, current_user_lon,
            mandi_lat, mandi_lon,
            api_key
        )

        if route2:
            folium.PolyLine(
                route2,
                color='darkorange',
                weight=5,
                opacity=0.6,
                popup='User to Mandi'
            ).add_to(m)

            # Collect traffic data for quantum evaluation
            traffic_ratios = []
            sample_points = []
            sample_rate = max(1, len(route2)) // 5  # Sample 5 points

            for i, (lat, lon) in enumerate(route2):
                if i % sample_rate == 0:
                    color = get_traffic_color(lat, lon, api_key)
                    ratio = 0.9 if color == 'green' else 0.6 if color == 'orange' else 0.3
                    traffic_ratios.append(ratio)
                    sample_points.append((lat, lon))
                    time.sleep(0.1)

            # Run quantum evaluation if we have enough points
            if len(traffic_ratios) >= 2:
                # 1) Predict delay in minutes via your QDelay module
                predicted_delay = quantum_delay_prediction(
                    traffic_ratios,
                    trained_thetas=PRETRAINED_THETAS,  # from your top‐of‐file import
                    max_delay=45.0                     # adjust as needed
                )

                # 2) Unpack the last sample point for accurate placement
                lat, lon = sample_points[-1]

                # 3) Render a small info‐card at that point
                card_html = f"""
                <div style="
                    padding:6px 10px;
                    font-family:Arial, sans-serif;
                    text-align:center;
                ">
                    <strong style="font-size:13px;">अनुमानित विलंब</strong><br>
                    <span style="font-size:15px; color:blue;">
                        ⏱ {predicted_delay:.1f} min
                    </span>
                </div>
                """

                folium.Marker(
                    location=[lat, lon],
                    icon=folium.DivIcon(html=card_html)
                ).add_to(m)

            # Add traffic-colored segments
            segment_size = 3  # Check traffic every N points
            colored_segments = []
            current_segment = []
            current_color = None

            for i, (lat, lon) in enumerate(route2):
                if i % segment_size == 0:
                    color = get_traffic_color(lat, lon, api_key)
                    if current_color is None:
                        current_color = color
                    
                    if color != current_color and current_segment:
                        colored_segments.append((current_color, current_segment))
                        current_segment = [(lat, lon)]
                        current_color = color
                    else:
                        current_segment.append((lat, lon))
                    time.sleep(0.1)
                else:
                    current_segment.append((lat, lon))

            if current_segment:
                colored_segments.append((current_color, current_segment))

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
        font-size: 20px;
    ">
        <b>मानचित्र मार्गदर्शिका</b><br>
        <span style="color:red;">🚚</span> निकटतम ट्रक स्थान<br>
        <span style="color:blue;">➤</span> चलती ट्रक की ऐनिमेशन<br>
        <span style="color:green;">🚚</span> अन्य ट्रक<br>
        <span style="color:orange;">🛒</span> मंडी (बाज़ार)<br>
        <span style="color:blue;">👤</span> उपयोगकर्ता स्थान<br>
        <hr style="margin:5px 0">
        <b>यातायात रंग संकेत</b><br>
        <span style="color:green;">▉</span> अच्छा यातायात (90% से अधिक गति)<br>
        <span style="color:orange;">▉</span> मध्यम यातायात (60-90% गति)<br>
        <span style="color:red;">▉</span> भारी यातायात (60% से कम गति)<br>
        <span style="color:grey;">▉</span> कोई डेटा नहीं<br>
        <span style="color:purple;">▉</span> क्वांटम-मूल्यांकित<br>
        <hr style="margin:5px 0">
        <b>निकटतम ट्रक</b>: {truck_info}

    </div>
    """.format(
        truck_info=f"{distance_km:.2f} किमी, अनुमानित समय: {time_minutes:.0f} मिनट"
        if distance_km and time_minutes else "उपलब्ध नहीं"
    )


    
    m.get_root().html.add_child(folium.Element(legend_html))
    return m._repr_html_()

if __name__ == "__main__":
    app.run(debug=True, port=5000)