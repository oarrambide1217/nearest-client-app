from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2
import pandas as pd

app = Flask(__name__)

stores_df = pd.read_csv("client_stores.csv")
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
    data = request.get_json()
    address = data.get("address")

    if not address:
        return jsonify({"error": "Address required"}), 400

    location = geolocator.geocode(address)
    if not location:
        return jsonify({"error": "Address not found"}), 400

    lat, lon = location.latitude, location.longitude
    results = []

    for _, row in stores_df.iterrows():
        distance = haversine_miles(lat, lon, row["Latitude"], row["Longitude"])
        results.append({
            "store_name": row["Client"],
            "address": row["Address"],
            "distance": round(distance, 2)
        })

    results.sort(key=lambda x: x["distance"])

    return jsonify({
        "input_address": address,
        "closest": results[0],
        "top_3": results[:3]
    })

if __name__ == "__main__":
    app.run(debug=True)