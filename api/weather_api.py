from flask import Flask, request, jsonify, abort
import requests
# import os

app = Flask(__name__)

# Map WMO weather codes to descriptions and rainy flag
def map_weather_code(code: int):
    is_rainy = False
    if code == 0:
        desc = "Clear"
    elif code == 1:
        desc = "Mostly clear"
    elif code == 2:
        desc = "Partly cloudy"
    elif code == 3:
        desc = "Overcast"
    elif code == 45:
        desc = "Fog"
    elif code == 46:
        desc = "Fog, visibility increasing"
    elif code == 47:
        desc = "Fog, visibility not improving"
    elif code == 48:
        desc = "Fog with frost deposit, visibility improving"
    elif code == 49:
        desc = "Fog with frost deposit, visibility not improving"
    elif code in (51, 53, 55):
        desc = "Drizzle"
        is_rainy = True
    elif 61 <= code <= 67:
        desc = "Rain"
        is_rainy = True
    elif 71 <= code <= 77:
        desc = "Snowfall"
    elif 80 <= code <= 82:
        desc = "Showers"
        is_rainy = True
    elif 85 <= code <= 86:
        desc = "Snow showers"
    elif code == 95:
        desc = "Thunderstorm"
        is_rainy = True
    elif code in (96, 99):
        desc = "Thunderstorm with hail"
        is_rainy = True
    else:
        desc = "Undefined weather condition"
    return desc, is_rainy

@app.route('/weatherbysearch', methods=['GET'])
def weather_endpoint():
    # Default to Turin if no search provided
    city = request.args.get('search', 'Turin')

    # 1. Geocoding via Open-Meteo
    geo_url = (
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    )
    geo_resp = requests.get(geo_url)
    if geo_resp.status_code != 200:
        abort(502, description="Error during geocoding")
    geo_data = geo_resp.json()
    results = geo_data.get('results') or geo_data.get('features') or []
    if not results:
        abort(404, description="Location not found")
    loc = results[0]
    # Open-Meteo geocoding returns 'latitude', 'longitude', 'elevation'
    lat = loc.get('latitude')
    lon = loc.get('longitude')
    elevation = loc.get('elevation', 0.0)
    # If name field differs, use 'name' or 'formatted'
    location_name = loc.get('name') or loc.get('formatted') or city

    # 2. Weather fetch via Open-Meteo
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,weathercode,wind_speed_10m,precipitation"
    )
    weather_resp = requests.get(weather_url)
    if weather_resp.status_code != 200:
        abort(502, description="Error fetching weather data")
    weather_data = weather_resp.json()
    current = weather_data.get('current')
    if not current:
        abort(500, description="Incomplete weather data")

    code = current.get('weathercode')
    temp = current.get('temperature_2m')
    humidity = current.get('relative_humidity_2m')
    precipitation = current.get('precipitation', 0.0)
    desc, is_rainy = map_weather_code(code)

    result = {
        'location': location_name,
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'temperature': temp,
        'humidity': humidity,
        'weather_code': code,
        'weather_desc': desc,
        'precipitation': precipitation,
        'is_rainy': is_rainy
    }
    return jsonify(result)

@app.route('/weatherbycoordinates', methods=['GET'])
def weather_by_coordinates():
    try:
        lat = float(request.args.get('latitude'))
        lon = float(request.args.get('longitude'))
    except (TypeError, ValueError):
        abort(400, description="Latitude and longitude parameters are invalid or missing")

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,weathercode,wind_speed_10m,precipitation"
    )
    weather_resp = requests.get(weather_url)
    if weather_resp.status_code != 200:
        abort(502, description="Error fetching weather data")

    weather_data = weather_resp.json()
    current = weather_data.get('current')
    if not current:
        abort(500, description="Incomplete weather data")

    code = current.get('weathercode')
    temp = current.get('temperature_2m')
    humidity = current.get('relative_humidity_2m')
    precipitation = current.get('precipitation', 0.0)
    desc, is_rainy = map_weather_code(code)

    result = {
        'latitude': lat,
        'longitude': lon,
        'temperature': temp,
        'humidity': humidity,
        'weather_code': code,
        'weather_desc': desc,
        'precipitation': precipitation,
        'is_rainy': is_rainy
    }

    return jsonify(result)

@app.route('/weather', methods=['GET'])
def unified_weather():
    search = request.args.get('search')
    # Accept both parameter naming styles: latitude/longitude and lat/long
    lat = request.args.get('latitude') or request.args.get('lat')
    lon = request.args.get('longitude') or request.args.get('long')

    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
            location_name = f"{lat},{lon}"
            elevation = 0.0  # Not available from direct lat/lon, could use another API
        except ValueError:
            abort(400, description="Invalid latitude or longitude")
    else:
        # Default to Turin if no search is provided
        city = search or 'Turin'
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_resp = requests.get(geo_url)
        if geo_resp.status_code != 200:
            abort(502, description="Error during geocoding")
        geo_data = geo_resp.json()
        results = geo_data.get('results') or []
        if not results:
            abort(404, description="Location not found")
        loc = results[0]
        lat = loc.get('latitude')
        lon = loc.get('longitude')
        elevation = loc.get('elevation', 0.0)
        location_name = loc.get('name') or city

    # Fetch weather data
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,weathercode,wind_speed_10m,precipitation"
    )
    weather_resp = requests.get(weather_url)
    if weather_resp.status_code != 200:
        abort(502, description="Error fetching weather data")
    weather_data = weather_resp.json()
    current = weather_data.get('current')
    if not current:
        abort(500, description="Incomplete weather data")

    code = current.get('weathercode')
    temp = current.get('temperature_2m')
    humidity = current.get('relative_humidity_2m')
    precipitation = current.get('precipitation', 0.0)
    desc, is_rainy = map_weather_code(code)

    result = {
        'location': location_name,
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'temperature': temp,
        'humidity': humidity,
        'weather_code': code,
        'weather_desc': desc,
        'precipitation': precipitation,
        'is_rainy': is_rainy
    }

    return jsonify(result)


# if __name__ == '__main__':
#     # Run locally on localhost:5000 (default Flask port)
#     app.run(debug=True, host='127.0.0.1', port=5000)
