from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2
from urllib.parse import quote
import pandas as pd
import os

app = Flask(__name__)

CSV_FILE = "Spa Surge Client Locations with geocodes, March 20 update v2.csv"

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"Could not find CSV file: {CSV_FILE}")

stores_df = pd.read_csv(CSV_FILE)
geolocator = Nominatim(user_agent="nearest_client_app")

def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return r * c

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/nearest-client", methods=["POST"])
def nearest_client():
    data = request.get_json(silent=True) or {}
    address = (data.get("address") or "").strip()

    if not address:
        return jsonify({"error": "Address required"}), 400

    try:
        location = geolocator.geocode(address, timeout=10)
        if not location:
            return jsonify({"error": "Address not found"}), 400

        lat, lon = location.latitude, location.longitude
        results = []

        for _, row in stores_df.iterrows():
            try:
                store_lat = float(row["Latitude"])
                store_lon = float(row["Longitude"])
            except Exception:
                continue

            client_name = str(row.get("Client", "")).strip()
            store_address = str(row.get("Address", "")).strip()

            if not client_name or not store_address:
                continue

            dist = haversine_miles(lat, lon, store_lat, store_lon)

            results.append({
                "store_name": client_name,
                "address": store_address,
                "distance": round(dist, 2)
            })

        if not results:
            return jsonify({"error": "No valid store coordinates found in CSV"}), 500

        results.sort(key=lambda x: x["distance"])
        closest = results[0]

        if closest["distance"] < 10:
            insight = "⚠️ Very close to an existing client — potential overlap risk."
        elif closest["distance"] < 25:
            insight = "⚠️ Moderate proximity — review territory overlap before targeting."
        else:
            insight = "✅ Good expansion opportunity — low overlap risk."

        maps_link = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={quote(address)}"
            f"&destination={quote(closest['address'])}"
        )

        return jsonify({
            "input_address": address,
            "closest": closest,
            "top_3": results[:3],
            "insight": insight,
            "maps_link": maps_link
        })

    except Exception as e:
        print("ERROR in /nearest-client:", str(e), flush=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run()