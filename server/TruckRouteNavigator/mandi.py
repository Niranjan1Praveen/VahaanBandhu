import os
from flask import Flask
import folium
from supabase import create_client
from dotenv import load_dotenv

# Load .env for SUPABASE keys
load_dotenv()
app = Flask(__name__)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/mandi-map")
def mandi_map():
    # Set default map center (India)
    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5)

    # Fetch all mandi points
    data = supabase.table("MandiLatLong").select("*").execute().data or []

    for mandi in data:
        lat = mandi.get("Latitude")
        lon = mandi.get("Longitude")
        name = mandi.get("Mandi")
        name_hindi = mandi.get("Mandi_Hindi")
        state = mandi.get("State")

        if lat is not None and lon is not None:
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{name}</b><br>{name_hindi}<br>{state}",
                icon=folium.Icon(color="darkpurple", icon="shopping-cart", prefix="fa")
            ).add_to(m)

    return m._repr_html_()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
