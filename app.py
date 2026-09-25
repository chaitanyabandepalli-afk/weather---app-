"""
Weather Forecast Analysis Using Statistics and Probability
Flask Backend — All calculations happen here, no database.

Data flow:
  1. User clicks "Analyze & Predict"
  2. Frontend POSTs city + year range to /api/analyze
  3. Backend fetches historical daily weather from Open-Meteo Archive API
  4. Backend computes Mean, Median, Mode, Variance, Std Dev, Probability,
     Normal Distribution, Time-Series regression, and Future Predictions
  5. Returns everything as JSON — frontend only renders charts/tables
"""

import math
from datetime import datetime, timedelta
from collections import Counter
import difflib

from flask import Flask, render_template, request, jsonify
import requests
import numpy as np

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Pre-configured cities with verified coordinates across India and globally
# ---------------------------------------------------------------------------
INDIAN_AND_GLOBAL_CITIES = [
    # Top Metros & Indian Capitals
    {"name": "Hyderabad",     "country": "India", "state": "Telangana",       "lat": 17.3850, "lon": 78.4867},
    {"name": "Mumbai",        "country": "India", "state": "Maharashtra",     "lat": 19.0760, "lon": 72.8777},
    {"name": "Delhi",         "country": "India", "state": "Delhi",           "lat": 28.6139, "lon": 77.2090},
    {"name": "Bengaluru",     "country": "India", "state": "Karnataka",       "lat": 12.9716, "lon": 77.5946},
    {"name": "Chennai",       "country": "India", "state": "Tamil Nadu",      "lat": 13.0827, "lon": 80.2707},
    {"name": "Kolkata",       "country": "India", "state": "West Bengal",     "lat": 22.5726, "lon": 88.3639},
    {"name": "Pune",          "country": "India", "state": "Maharashtra",     "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad",     "country": "India", "state": "Gujarat",         "lat": 23.0225, "lon": 72.5714},
    {"name": "Jaipur",        "country": "India", "state": "Rajasthan",       "lat": 26.9124, "lon": 75.7873},
    {"name": "Surat",         "country": "India", "state": "Gujarat",         "lat": 21.1702, "lon": 72.8311},
    {"name": "Lucknow",       "country": "India", "state": "Uttar Pradesh",   "lat": 26.8467, "lon": 80.9462},
    {"name": "Kanpur",        "country": "India", "state": "Uttar Pradesh",   "lat": 26.4499, "lon": 80.3319},
    {"name": "Nagpur",        "country": "India", "state": "Maharashtra",     "lat": 21.1458, "lon": 79.0882},
    {"name": "Indore",        "country": "India", "state": "Madhya Pradesh",  "lat": 22.7196, "lon": 75.8577},
    {"name": "Bhopal",        "country": "India", "state": "Madhya Pradesh",  "lat": 23.2599, "lon": 77.4126},
    {"name": "Visakhapatnam", "country": "India", "state": "Andhra Pradesh",  "lat": 17.6868, "lon": 83.2185},
    {"name": "Patna",         "country": "India", "state": "Bihar",           "lat": 25.5941, "lon": 85.1376},
    {"name": "Vadodara",      "country": "India", "state": "Gujarat",         "lat": 22.3072, "lon": 73.1812},
    {"name": "Ludhiana",      "country": "India", "state": "Punjab",          "lat": 30.9010, "lon": 75.8573},
    {"name": "Agra",          "country": "India", "state": "Uttar Pradesh",   "lat": 27.1767, "lon": 78.0081},
    {"name": "Nashik",        "country": "India", "state": "Maharashtra",     "lat": 19.9975, "lon": 73.7898},
    {"name": "Varanasi",      "country": "India", "state": "Uttar Pradesh",   "lat": 25.3176, "lon": 82.9739},
    {"name": "Srinagar",      "country": "India", "state": "Jammu & Kashmir", "lat": 34.0837, "lon": 74.7973},
    {"name": "Aurangabad",    "country": "India", "state": "Maharashtra",     "lat": 19.8762, "lon": 75.3433},
    {"name": "Dhanbad",       "country": "India", "state": "Jharkhand",       "lat": 23.7957, "lon": 86.4304},
    {"name": "Amritsar",      "country": "India", "state": "Punjab",          "lat": 31.6340, "lon": 74.8723},
    {"name": "Prayagraj",     "country": "India", "state": "Uttar Pradesh",   "lat": 25.4358, "lon": 81.8463},
    {"name": "Ranchi",        "country": "India", "state": "Jharkhand",       "lat": 23.3441, "lon": 85.3096},
    {"name": "Coimbatore",    "country": "India", "state": "Tamil Nadu",      "lat": 11.0168, "lon": 76.9558},
    {"name": "Jabalpur",      "country": "India", "state": "Madhya Pradesh",  "lat": 23.1815, "lon": 79.9864},
    {"name": "Gwalior",       "country": "India", "state": "Madhya Pradesh",  "lat": 26.2183, "lon": 78.1828},
    {"name": "Vijayawada",    "country": "India", "state": "Andhra Pradesh",  "lat": 16.5062, "lon": 80.6480},
    {"name": "Jodhpur",       "country": "India", "state": "Rajasthan",       "lat": 26.2389, "lon": 73.0243},
    {"name": "Madurai",       "country": "India", "state": "Tamil Nadu",      "lat": 9.9252,  "lon": 78.1198},
    {"name": "Raipur",        "country": "India", "state": "Chhattisgarh",    "lat": 21.2514, "lon": 81.6296},
    {"name": "Kota",          "country": "India", "state": "Rajasthan",       "lat": 25.2138, "lon": 75.8648},
    {"name": "Guwahati",      "country": "India", "state": "Assam",           "lat": 26.1445, "lon": 91.7362},
    {"name": "Chandigarh",    "country": "India", "state": "Chandigarh",      "lat": 30.7333, "lon": 76.7794},
    {"name": "Solapur",       "country": "India", "state": "Maharashtra",     "lat": 17.6599, "lon": 75.9064},
    {"name": "Mysuru",        "country": "India", "state": "Karnataka",       "lat": 12.2958, "lon": 76.6394},
    {"name": "Tiruchirappalli","country":"India", "state": "Tamil Nadu",      "lat": 10.7905, "lon": 78.7047},
    {"name": "Bareilly",      "country": "India", "state": "Uttar Pradesh",   "lat": 28.3670, "lon": 79.4304},
    {"name": "Aligarh",       "country": "India", "state": "Uttar Pradesh",   "lat": 27.8974, "lon": 78.0880},
    {"name": "Tiruppur",      "country": "India", "state": "Tamil Nadu",      "lat": 11.1085, "lon": 77.3411},
    {"name": "Moradabad",     "country": "India", "state": "Uttar Pradesh",   "lat": 28.8351, "lon": 78.7749},
    {"name": "Jalandhar",     "country": "India", "state": "Punjab",          "lat": 31.3260, "lon": 75.5762},
    {"name": "Bhubaneswar",   "country": "India", "state": "Odisha",          "lat": 20.2961, "lon": 85.8245},
    {"name": "Salem",         "country": "India", "state": "Tamil Nadu",      "lat": 11.6643, "lon": 78.1460},
    {"name": "Warangal",      "country": "India", "state": "Telangana",       "lat": 17.9689, "lon": 79.5941},
    {"name": "Guntur",        "country": "India", "state": "Andhra Pradesh",  "lat": 16.3067, "lon": 80.4365},
    {"name": "Thiruvananthapuram","country":"India","state":"Kerala",         "lat": 8.5241,  "lon": 76.9366},
    {"name": "Kochi",         "country": "India", "state": "Kerala",          "lat": 9.9312,  "lon": 76.2673},
    {"name": "Gorakhpur",     "country": "India", "state": "Uttar Pradesh",   "lat": 26.7606, "lon": 83.3732},
    {"name": "Bikaner",       "country": "India", "state": "Rajasthan",       "lat": 28.0229, "lon": 73.3119},
    {"name": "Amravati",      "country": "India", "state": "Maharashtra",     "lat": 20.9374, "lon": 77.7796},
    {"name": "Noida",         "country": "India", "state": "Uttar Pradesh",   "lat": 28.5355, "lon": 77.3910},
    {"name": "Jamshedpur",    "country": "India", "state": "Jharkhand",       "lat": 22.8046, "lon": 86.2029},
    {"name": "Bhilai",        "country": "India", "state": "Chhattisgarh",    "lat": 21.1938, "lon": 81.3509},
    {"name": "Cuttack",       "country": "India", "state": "Odisha",          "lat": 20.4625, "lon": 85.8828},
    {"name": "Dehradun",      "country": "India", "state": "Uttarakhand",     "lat": 30.3165, "lon": 78.0322},
    {"name": "Kozhikode",     "country": "India", "state": "Kerala",          "lat": 11.2588, "lon": 75.7804},
    {"name": "Rourkela",      "country": "India", "state": "Odisha",          "lat": 22.2604, "lon": 84.8536},
    {"name": "Kolhapur",      "country": "India", "state": "Maharashtra",     "lat": 16.7050, "lon": 74.2433},
    {"name": "Ajmer",         "country": "India", "state": "Rajasthan",       "lat": 26.4499, "lon": 74.6399},
    {"name": "Jamnagar",      "country": "India", "state": "Gujarat",         "lat": 22.4707, "lon": 70.0577},
    {"name": "Ujjain",        "country": "India", "state": "Madhya Pradesh",  "lat": 23.1765, "lon": 75.7885},
    {"name": "Siliguri",      "country": "India", "state": "West Bengal",     "lat": 26.7271, "lon": 88.3953},
    {"name": "Jhansi",        "country": "India", "state": "Uttar Pradesh",   "lat": 25.4484, "lon": 78.5685},
    {"name": "Nellore",       "country": "India", "state": "Andhra Pradesh",  "lat": 14.4426, "lon": 79.9865},
    {"name": "Jammu",         "country": "India", "state": "Jammu & Kashmir", "lat": 32.7266, "lon": 74.8570},
    {"name": "Mangaluru",     "country": "India", "state": "Karnataka",       "lat": 12.9141, "lon": 74.8560},
    {"name": "Belagavi",      "country": "India", "state": "Karnataka",       "lat": 15.8497, "lon": 74.4977},
    {"name": "Tirupati",      "country": "India", "state": "Andhra Pradesh",  "lat": 13.6288, "lon": 79.4192},
    {"name": "Kurnool",       "country": "India", "state": "Andhra Pradesh",  "lat": 15.8281, "lon": 78.0373},
    {"name": "Rajahmundry",   "country": "India", "state": "Andhra Pradesh",  "lat": 17.0005, "lon": 81.8040},
    {"name": "Kakinada",      "country": "India", "state": "Andhra Pradesh",  "lat": 16.9891, "lon": 82.2475},
    {"name": "Narasaraopet",  "country": "India", "state": "Andhra Pradesh",  "lat": 16.2359, "lon": 80.0499},
    {"name": "Kadapa",        "country": "India", "state": "Andhra Pradesh",  "lat": 14.4673, "lon": 78.8242},
    {"name": "Anantapur",     "country": "India", "state": "Andhra Pradesh",  "lat": 14.6819, "lon": 77.6006},
    {"name": "Eluru",         "country": "India", "state": "Andhra Pradesh",  "lat": 16.7107, "lon": 81.0952},
    {"name": "Shimla",        "country": "India", "state": "Himachal Pradesh","lat": 31.1048, "lon": 77.1734},
    {"name": "Panaji",        "country": "India", "state": "Goa",             "lat": 15.4909, "lon": 73.8278},
    {"name": "Gurugram",      "country": "India", "state": "Haryana",         "lat": 28.4595, "lon": 77.0266},
    {"name": "Haridwar",      "country": "India", "state": "Uttarakhand",     "lat": 29.9457, "lon": 78.1642},
    {"name": "Udaipur",       "country": "India", "state": "Rajasthan",       "lat": 24.5854, "lon": 73.7125},
    {"name": "Nizamabad",     "country": "India", "state": "Telangana",       "lat": 18.6725, "lon": 78.0941},
    {"name": "Khammam",       "country": "India", "state": "Telangana",       "lat": 17.2473, "lon": 80.1514},
    {"name": "Karimnagar",    "country": "India", "state": "Telangana",       "lat": 18.4386, "lon": 79.1288},
    # Top Global Cities
    {"name": "London",        "country": "United Kingdom", "lat": 51.5074,     "lon": -0.1278},
    {"name": "New York",      "country": "United States",  "lat": 40.7128,     "lon": -74.0060},
    {"name": "Tokyo",         "country": "Japan",          "lat": 35.6762,     "lon": 139.6503},
    {"name": "Sydney",        "country": "Australia",      "lat": -33.8688,    "lon": 151.2093},
    {"name": "Dubai",         "country": "United Arab Emirates", "lat": 25.2048,"lon": 55.2708},
    {"name": "Paris",         "country": "France",         "lat": 48.8566,     "lon": 2.3522},
    {"name": "Singapore",     "country": "Singapore",      "lat": 1.3521,      "lon": 103.8198},
]

DEFAULT_CITIES = INDIAN_AND_GLOBAL_CITIES[:10]

# Common aliases, typos, and historical names mapped to canonical city names
CITY_ALIASES = {
    "mumabai": "Mumbai",
    "mumbay": "Mumbai",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "hydrabad": "Hyderabad",
    "hyderbad": "Hyderabad",
    "secunderabad": "Hyderabad",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "banglore": "Bengaluru",
    "calcutta": "Kolkata",
    "kolkatta": "Kolkata",
    "madras": "Chennai",
    "chenai": "Chennai",
    "vizag": "Visakhapatnam",
    "visakhapatnam": "Visakhapatnam",
    "vishakhapatnam": "Visakhapatnam",
    "poona": "Pune",
    "baroda": "Vadodara",
    "cochin": "Kochi",
    "trivandrum": "Thiruvananthapuram",
    "banaras": "Varanasi",
    "kashi": "Varanasi",
    "allahabad": "Prayagraj",
    "gurgaon": "Gurugram",
    "delh": "Delhi",
    "new delhi": "Delhi",
    "jaipoor": "Jaipur",
    "mysore": "Mysuru",
    "simla": "Shimla",
    "marasaraopet": "Narasaraopet",
    "narasaraopeta": "Narasaraopet",
}


def resolve_city(query):
    """
    Resolves any city query (handles typos, common aliases, Indian cities,
    global cities, or queries Open-Meteo Geocoding API).
    Returns a dict with {"name", "country", "lat", "lon"}.
    """
    if not query:
        return INDIAN_AND_GLOBAL_CITIES[0]

    q_clean = query.strip()
    q_lower = q_clean.lower()

    # 1. Direct alias match
    if q_lower in CITY_ALIASES:
        canonical = CITY_ALIASES[q_lower]
        for c in INDIAN_AND_GLOBAL_CITIES:
            if c["name"].lower() == canonical.lower():
                return c

    # 2. Exact match in city database
    for c in INDIAN_AND_GLOBAL_CITIES:
        if c["name"].lower() == q_lower:
            return c

    # 3. Substring match
    for c in INDIAN_AND_GLOBAL_CITIES:
        if q_lower in c["name"].lower() or c["name"].lower() in q_lower:
            return c

    # 4. Fuzzy match against aliases + city names
    all_keys = list(CITY_ALIASES.keys()) + [c["name"].lower() for c in INDIAN_AND_GLOBAL_CITIES]
    matches = difflib.get_close_matches(q_lower, all_keys, n=1, cutoff=0.5)
    if matches:
        matched_key = matches[0]
        canonical = CITY_ALIASES.get(matched_key, matched_key)
        for c in INDIAN_AND_GLOBAL_CITIES:
            if c["name"].lower() == canonical.lower():
                return c

    # 5. Fallback: Query Open-Meteo Geocoding API
    try:
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search?"
            f"name={requests.utils.quote(q_clean)}&count=5&language=en&format=json"
        )
        resp = requests.get(geo_url, timeout=5)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                top = results[0]
                return {
                    "name":    top.get("name"),
                    "country": top.get("country", ""),
                    "lat":     float(top.get("latitude")),
                    "lon":     float(top.get("longitude")),
                }
    except Exception as e:
        print(f"[Resolve City] Geocoding fallback error: {e}")

    # 6. Default to first city if absolutely nothing found
    return INDIAN_AND_GLOBAL_CITIES[0]

# ---------------------------------------------------------------------------
# Fallback mock data generator (used only if API is unreachable)
# ---------------------------------------------------------------------------
def generate_mock_historical_data(city_name, start_year, end_year):
    """
    Generates realistic synthetic weather data when the Open-Meteo API
    is unavailable.  Uses numpy's RNG so results are reproducible.
    """
    rng = np.random.default_rng(seed=abs(hash(city_name)) % 2**31)

    profiles = {
        "Hyderabad":  {"temp_base": 29.5, "temp_amp": 6.0,  "rain_prob": 0.28, "hum_base": 62},
        "Mumbai":     {"temp_base": 27.5, "temp_amp": 4.0,  "rain_prob": 0.35, "hum_base": 75},
        "Delhi":      {"temp_base": 25.0, "temp_amp": 12.0, "rain_prob": 0.22, "hum_base": 55},
        "Bengaluru":  {"temp_base": 24.0, "temp_amp": 4.5,  "rain_prob": 0.30, "hum_base": 65},
        "Chennai":    {"temp_base": 28.5, "temp_amp": 4.0,  "rain_prob": 0.30, "hum_base": 72},
        "Kolkata":    {"temp_base": 26.5, "temp_amp": 7.5,  "rain_prob": 0.32, "hum_base": 73},
        "London":     {"temp_base": 11.5, "temp_amp": 7.5,  "rain_prob": 0.42, "hum_base": 78},
        "New York":   {"temp_base": 13.0, "temp_amp": 13.0, "rain_prob": 0.33, "hum_base": 64},
        "Tokyo":      {"temp_base": 16.0, "temp_amp": 11.0, "rain_prob": 0.34, "hum_base": 68},
        "Sydney":     {"temp_base": 18.5, "temp_amp": 6.5,  "rain_prob": 0.31, "hum_base": 67},
    }
    prof = profiles.get(city_name,
                        {"temp_base": 25.0, "temp_amp": 8.0, "rain_prob": 0.30, "hum_base": 65})

    start_date = datetime(start_year, 1, 1)
    end_date   = datetime(end_year, 12, 31)
    cur = start_date
    records = []

    while cur <= end_date:
        doy = cur.timetuple().tm_yday
        year_offset = (cur.year - start_year) * 0.25

        seasonal = (prof["temp_base"] + year_offset
                     + prof["temp_amp"] * math.sin(2 * math.pi * (doy - 100) / 365))
        noise = rng.normal(0, 1.8)
        t_mean = round(seasonal + noise, 1)
        t_max  = round(t_mean + rng.uniform(3.0, 7.0), 1)
        t_min  = round(t_mean - rng.uniform(3.0, 7.0), 1)

        month = cur.month
        is_monsoon = (6 <= month <= 9) if prof["temp_base"] > 20 else (10 <= month <= 2 or month <= 2)
        boost = 0.35 if is_monsoon else 0.0

        will_rain = rng.random() < (prof["rain_prob"] + boost)
        precip = round(float(rng.exponential(14.0)) + 0.5, 1) if will_rain else 0.0
        hum = int(max(20, min(100, prof["hum_base"] + (25 if will_rain else -10) + rng.uniform(-10, 10))))
        wind = round(float(rng.uniform(5.0, 25.0)) + (5.0 if will_rain else 0.0), 1)

        records.append({
            "date":          cur.strftime("%Y-%m-%d"),
            "year":          cur.year,
            "month":         cur.month,
            "day":           cur.day,
            "month_name":    cur.strftime("%b"),
            "day_name":      cur.strftime("%a"),
            "temp_mean":     t_mean,
            "temp_max":      t_max,
            "temp_min":      t_min,
            "precipitation": precip,
            "humidity":      hum,
            "wind_speed":    wind,
        })
        cur += timedelta(days=1)

    return records, "Mock Engine (Offline Fallback)"


# ---------------------------------------------------------------------------
# Open-Meteo Historical Archive API fetcher
# ---------------------------------------------------------------------------
def fetch_open_meteo_data(city_name, lat, lon, start_year, end_year):
    """
    Fetches REAL historical daily weather records from the free
    Open-Meteo Historical Archive API.
    No API key required.

    API docs: https://open-meteo.com/en/docs/historical-weather-api
    Endpoint: https://archive-api.open-meteo.com/v1/archive

    Returns:
        (list[dict], str)  –  daily records + data source label
    """
    start_date = f"{start_year}-01-01"
    end_date   = f"{end_year}-12-31"

    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={start_date}&end_date={end_date}&"
        "daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,"
        "precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max&"
        "timezone=auto"
    )

    try:
        print(f"[API] Fetching {city_name} ({lat},{lon}) from {start_date} to {end_date} ...")
        resp = requests.get(url, timeout=20)
        print(f"[API] Response status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"[API] Non-200 response: {resp.text[:500]}")
            return generate_mock_historical_data(city_name, start_year, end_year)

        data = resp.json()
        daily = data.get("daily", {})
        times      = daily.get("time", [])
        temp_means = daily.get("temperature_2m_mean", [])
        temp_maxs  = daily.get("temperature_2m_max", [])
        temp_mins  = daily.get("temperature_2m_min", [])
        precips    = daily.get("precipitation_sum", [])
        humidities = daily.get("relative_humidity_2m_mean", [])
        winds      = daily.get("wind_speed_10m_max", [])

        if not times:
            print("[API] No 'time' array returned — falling back.")
            return generate_mock_historical_data(city_name, start_year, end_year)

        records = []
        for i in range(len(times)):
            dt = datetime.strptime(times[i], "%Y-%m-%d")

            t_mean = temp_means[i] if (i < len(temp_means) and temp_means[i] is not None) else None
            t_max  = temp_maxs[i]  if (i < len(temp_maxs)  and temp_maxs[i]  is not None) else None
            t_min  = temp_mins[i]  if (i < len(temp_mins)  and temp_mins[i]  is not None) else None
            precip = precips[i]    if (i < len(precips)    and precips[i]    is not None) else 0.0
            hum    = humidities[i] if (i < len(humidities) and humidities[i] is not None) else None
            wind   = winds[i]      if (i < len(winds)      and winds[i]      is not None) else None

            # If mean temp is missing, try to compute from max/min
            if t_mean is None:
                if t_max is not None and t_min is not None:
                    t_mean = round((t_max + t_min) / 2.0, 1)
                else:
                    continue  # skip days with no temperature at all

            if t_max is None:
                t_max = round(t_mean + 4.0, 1)
            if t_min is None:
                t_min = round(t_mean - 4.0, 1)
            if hum is None:
                hum = 65
            if wind is None:
                wind = 12.0

            records.append({
                "date":          times[i],
                "year":          dt.year,
                "month":         dt.month,
                "day":           dt.day,
                "month_name":    dt.strftime("%b"),
                "day_name":      dt.strftime("%a"),
                "temp_mean":     round(float(t_mean), 1),
                "temp_max":      round(float(t_max), 1),
                "temp_min":      round(float(t_min), 1),
                "precipitation": round(float(precip), 1),
                "humidity":      round(float(hum), 1),
                "wind_speed":    round(float(wind), 1),
            })

        total = len(records)
        print(f"[API] Successfully fetched {total} daily records for {city_name}")
        if total == 0:
            return generate_mock_historical_data(city_name, start_year, end_year)

        return records, f"Open-Meteo Historical Archive API (Live) — {total} records"

    except Exception as e:
        print(f"[API] Error for {city_name}: {e}")
        return generate_mock_historical_data(city_name, start_year, end_year)


# ---------------------------------------------------------------------------
# STATISTICS FUNCTIONS  (all the maths happens here)
# ---------------------------------------------------------------------------

def calculate_descriptive_stats(values, label="values"):
    """
    Computes the full set of descriptive statistics for a list of numbers:
      - Count N
      - Mean (μ)          = sum(x) / N
      - Median             = middle value after sorting
      - Mode               = most frequently occurring value (rounded to 1dp)
      - Variance (σ²)      = sum((x - μ)²) / N       (population variance)
      - Standard Dev (σ)   = sqrt(variance)
      - Min, Max, Range
      - Q1, Q3, IQR

    Also returns a human-readable 'steps' dict showing the working.
    """
    if not values:
        return {"n": 0, "mean": 0, "median": 0, "mode": 0,
                "variance": 0, "std_dev": 0, "min": 0, "max": 0,
                "range": 0, "iqr": 0, "q25": 0, "q75": 0, "steps": {}}

    arr = np.array(values, dtype=float)
    n = len(arr)

    # ---- Mean ----
    total_sum = float(np.sum(arr))
    mean_val = total_sum / n

    # ---- Median ----
    sorted_arr = np.sort(arr)
    if n % 2 == 1:
        median_val = float(sorted_arr[n // 2])
        median_step = f"Sorted data has {n} values (odd). Middle index = {n // 2}. Median = {round(median_val, 2)}"
    else:
        mid1, mid2 = float(sorted_arr[n // 2 - 1]), float(sorted_arr[n // 2])
        median_val = (mid1 + mid2) / 2.0
        median_step = (f"Sorted data has {n} values (even). "
                       f"Middle values at index {n//2-1} and {n//2}: {round(mid1,2)} and {round(mid2,2)}. "
                       f"Median = ({round(mid1,2)} + {round(mid2,2)}) / 2 = {round(median_val, 2)}")

    # ---- Mode ----
    # Round to 1 decimal for continuous data to find meaningful mode
    rounded = [round(float(v), 1) for v in values]
    freq = Counter(rounded)
    max_freq = max(freq.values())
    modes = sorted([val for val, cnt in freq.items() if cnt == max_freq])
    mode_val = modes[0]  # take lowest mode if multimodal
    mode_step = f"Most frequent value (rounded to 1dp): {mode_val} (appears {max_freq} times)"

    # ---- Variance ----
    deviations_sq = (arr - mean_val) ** 2
    variance_val = float(np.sum(deviations_sq)) / n

    # ---- Standard Deviation ----
    std_dev_val = math.sqrt(variance_val)

    # ---- Min / Max / Range ----
    min_val  = float(np.min(arr))
    max_val  = float(np.max(arr))
    range_val = max_val - min_val

    # ---- Quartiles / IQR ----
    q25 = float(np.percentile(arr, 25))
    q75 = float(np.percentile(arr, 75))
    iqr = q75 - q25

    # ---- Build step-by-step explanation ----
    steps = {
        "mean": (f"Mean = Sum of all {label} / N = {round(total_sum, 2)} / {n} = {round(mean_val, 2)}"),
        "median": median_step,
        "mode": mode_step,
        "variance": (f"Variance = Σ(xi − μ)² / N = {round(float(np.sum(deviations_sq)), 2)} / {n} "
                     f"= {round(variance_val, 2)}"),
        "std_dev": f"Std Dev = √(Variance) = √({round(variance_val, 2)}) = {round(std_dev_val, 2)}",
        "range": f"Range = Max − Min = {round(max_val, 2)} − {round(min_val, 2)} = {round(range_val, 2)}",
        "iqr": f"IQR = Q3 − Q1 = {round(q75, 2)} − {round(q25, 2)} = {round(iqr, 2)}",
    }

    return {
        "n":        n,
        "mean":     round(mean_val, 2),
        "median":   round(median_val, 2),
        "mode":     round(mode_val, 1),
        "variance": round(variance_val, 2),
        "std_dev":  round(std_dev_val, 2),
        "min":      round(min_val, 2),
        "max":      round(max_val, 2),
        "range":    round(range_val, 2),
        "iqr":      round(iqr, 2),
        "q25":      round(q25, 2),
        "q75":      round(q75, 2),
        "steps":    steps,
    }


def perform_linear_regression(x_vals, y_vals):
    """
    Simple Linear Regression:  y = m·x + c

    m = (N·Σxy − Σx·Σy) / (N·Σx² − (Σx)²)
    c = (Σy − m·Σx) / N
    R² = 1 − SS_res / SS_tot
    """
    x = np.array(x_vals, dtype=float)
    y = np.array(y_vals, dtype=float)
    n = len(x)

    if n < 2:
        return {"slope": 0, "intercept": 0, "r_squared": 0,
                "equation": "y = 0x + 0", "step": "Not enough data points"}

    sum_x  = float(np.sum(x))
    sum_y  = float(np.sum(y))
    sum_xy = float(np.sum(x * y))
    sum_x2 = float(np.sum(x ** 2))

    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return {"slope": 0, "intercept": round(float(np.mean(y)), 4),
                "r_squared": 0, "equation": f"y = {round(float(np.mean(y)), 2)}",
                "step": "All x-values are identical; slope is 0."}

    m = (n * sum_xy - sum_x * sum_y) / denom
    c = (sum_y - m * sum_x) / n

    y_pred = m * x + c
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res = float(np.sum((y - y_pred) ** 2))
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    step_text = (
        f"N={n}, Σx={round(sum_x,2)}, Σy={round(sum_y,2)}, "
        f"Σxy={round(sum_xy,2)}, Σx²={round(sum_x2,2)}\n"
        f"m = (N·Σxy − Σx·Σy) / (N·Σx² − (Σx)²) = "
        f"({n}×{round(sum_xy,2)} − {round(sum_x,2)}×{round(sum_y,2)}) / "
        f"({n}×{round(sum_x2,2)} − {round(sum_x,2)}²) = {round(m,4)}\n"
        f"c = (Σy − m·Σx) / N = ({round(sum_y,2)} − {round(m,4)}×{round(sum_x,2)}) / {n} = {round(c,4)}\n"
        f"R² = 1 − SS_res/SS_tot = 1 − {round(ss_res,2)}/{round(ss_tot,2)} = {round(max(0,r2),4)}"
    )

    return {
        "slope":     round(float(m), 4),
        "intercept": round(float(c), 4),
        "r_squared": round(float(max(0, r2)), 4),
        "equation":  f"y = {round(float(m), 4)}·x + {round(float(c), 4)}",
        "step":      step_text,
    }


def fit_normal_distribution(values, num_points=80):
    """
    Fits a Gaussian bell curve  N(μ, σ²)  to the temperature data.
    PDF:  f(x) = (1 / (σ√(2π))) · exp(−½·((x−μ)/σ)²)
    """
    if not values:
        return {}

    arr = np.array(values, dtype=float)
    mu  = float(np.mean(arr))
    sigma = float(np.std(arr))
    if sigma == 0:
        sigma = 0.001

    x_min = mu - 4.0 * sigma
    x_max = mu + 4.0 * sigma
    xs = np.linspace(x_min, x_max, num_points)

    pdf_curve = []
    for x in xs:
        z = (x - mu) / sigma
        y = (1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * z * z)
        pdf_curve.append({"x": round(float(x), 2), "y": round(float(y), 6)})

    # Count values in each sigma band
    within_1s = int(np.sum(np.abs(arr - mu) <= sigma))
    within_2s = int(np.sum(np.abs(arr - mu) <= 2 * sigma))
    within_3s = int(np.sum(np.abs(arr - mu) <= 3 * sigma))
    n = len(arr)

    anomalies = [round(float(v), 1) for v in arr if abs(v - mu) > 2 * sigma]

    return {
        "pdf_curve": pdf_curve,
        "mean":      round(mu, 2),
        "std_dev":   round(sigma, 2),
        "sigma_1": {
            "low":  round(mu - sigma, 2),
            "high": round(mu + sigma, 2),
            "count": within_1s,
            "percentage": f"{round(within_1s / n * 100, 1)}%",
            "expected": "68.27%",
        },
        "sigma_2": {
            "low":  round(mu - 2 * sigma, 2),
            "high": round(mu + 2 * sigma, 2),
            "count": within_2s,
            "percentage": f"{round(within_2s / n * 100, 1)}%",
            "expected": "95.45%",
        },
        "sigma_3": {
            "low":  round(mu - 3 * sigma, 2),
            "high": round(mu + 3 * sigma, 2),
            "count": within_3s,
            "percentage": f"{round(within_3s / n * 100, 1)}%",
            "expected": "99.73%",
        },
        "anomaly_count": len(anomalies),
        "anomalies":     anomalies[:20],
    }


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cities", methods=["GET"])
def get_cities():
    """
    Returns city list. Searches via resolve_city and Open-Meteo Geocoding API.
    """
    query = request.args.get("query", "").strip()
    if query and len(query) >= 2:
        resolved = resolve_city(query)
        suggestions = []
        if resolved:
            suggestions.append(resolved)
        try:
            geo_url = (
                f"https://geocoding-api.open-meteo.com/v1/search?"
                f"name={requests.utils.quote(query)}&count=6&language=en&format=json"
            )
            resp = requests.get(geo_url, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for r in results:
                    name = r.get("name")
                    if not any(s["name"].lower() == name.lower() for s in suggestions):
                        suggestions.append({
                            "name":    name,
                            "country": r.get("country", ""),
                            "lat":     r.get("latitude"),
                            "lon":     r.get("longitude"),
                        })
        except Exception as e:
            print(f"[Geocoding] Search failed: {e}")

        if suggestions:
            return jsonify({"status": "success", "cities": suggestions[:6]})

    return jsonify({"status": "success", "cities": DEFAULT_CITIES})


@app.route("/api/analyze", methods=["POST"])
def analyze_weather():
    """
    MAIN ENDPOINT — does ALL the heavy lifting:
      1. Resolve city & coordinates (corrects typos like mumabai -> Mumbai)
      2. Fetch historical data from Open-Meteo API
      3. Compute descriptive stats (Mean, Median, Mode, Variance, StdDev)
      4. Compute rainfall probability
      5. Fit normal distribution
      6. Time-series regression & moving averages
      7. Predict future years using linear regression
      8. Return everything as JSON
    """
    payload    = request.get_json() or {}
    raw_city   = payload.get("city", "Hyderabad").strip()
    req_lat    = payload.get("lat")
    req_lon    = payload.get("lon")
    start_year = int(payload.get("start_year", 2021))
    end_year   = int(payload.get("end_year", 2025))

    # Always verify/resolve city coordinates so city name and coordinates NEVER mismatch
    resolved = resolve_city(raw_city)
    city_name = resolved["name"]
    if req_lat is not None and req_lon is not None and abs(float(req_lat) - resolved["lat"]) < 1.0:
        lat = float(req_lat)
        lon = float(req_lon)
    else:
        lat = resolved["lat"]
        lon = resolved["lon"]

    print(f"\n{'='*60}")
    print(f"[ANALYZE] Requested='{raw_city}' -> Resolved='{city_name}' ({lat}, {lon}), Range={start_year}-{end_year}")
    print(f"{'='*60}")

    # ── Step 1: Fetch historical data ──────────────────────────
    records, data_source = fetch_open_meteo_data(city_name, lat, lon, start_year, end_year)
    total_days = len(records)
    print(f"[ANALYZE] Got {total_days} daily records.  Source: {data_source}")

    # Extract numerical arrays
    temps     = [r["temp_mean"]     for r in records]
    temp_maxs = [r["temp_max"]      for r in records]
    temp_mins = [r["temp_min"]      for r in records]
    precips   = [r["precipitation"] for r in records]
    humids    = [r["humidity"]      for r in records]
    winds     = [r["wind_speed"]    for r in records]

    # ── Step 2: Descriptive statistics ─────────────────────────
    temp_stats   = calculate_descriptive_stats(temps,   "temperature values")
    precip_stats = calculate_descriptive_stats(precips, "precipitation values")
    humid_stats  = calculate_descriptive_stats(humids,  "humidity values")
    wind_stats   = calculate_descriptive_stats(winds,   "wind speed values")

    print(f"[STATS] Temperature — Mean={temp_stats['mean']}, Median={temp_stats['median']}, "
          f"Mode={temp_stats['mode']}, Var={temp_stats['variance']}, StdDev={temp_stats['std_dev']}")
    print(f"[STATS] Precipitation — Mean={precip_stats['mean']}, StdDev={precip_stats['std_dev']}")

    # ── Step 3: Rainfall probability ───────────────────────────
    rainy_records = [r for r in records if r["precipitation"] >= 0.5]
    dry_count     = total_days - len(rainy_records)
    rain_prob     = round(len(rainy_records) / total_days, 4) if total_days > 0 else 0.0
    rain_pct      = round(rain_prob * 100, 2)

    light_count  = len([r for r in records if 0.5 <= r["precipitation"] < 5.0])
    mod_count    = len([r for r in records if 5.0 <= r["precipitation"] < 20.0])
    heavy_count  = len([r for r in records if r["precipitation"] >= 20.0])

    prob_step = (
        f"P(Rain) = Rainy Days / Total Days = {len(rainy_records)} / {total_days} "
        f"= {rain_prob} = {rain_pct}%"
    )
    print(f"[PROB] {prob_step}")

    # ── Monthly breakdown ──────────────────────────────────────
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_buckets = {m: {"temps": [], "precips": [], "rain_days": 0, "total": 0}
                       for m in range(1, 13)}

    for r in records:
        mb = monthly_buckets[r["month"]]
        mb["temps"].append(r["temp_mean"])
        mb["precips"].append(r["precipitation"])
        mb["total"] += 1
        if r["precipitation"] >= 0.5:
            mb["rain_days"] += 1

    monthly_summary = []
    for m in range(1, 13):
        b = monthly_buckets[m]
        t = b["total"]
        rd = b["rain_days"]
        p = round(rd / t, 4) if t > 0 else 0.0
        avg_t = round(float(np.mean(b["temps"])), 2)  if b["temps"]  else 0.0
        tot_p = round(float(np.sum(b["precips"])), 1)  if b["precips"] else 0.0

        monthly_summary.append({
            "month_num":        m,
            "month_name":       month_names[m - 1],
            "avg_temp":         avg_t,
            "total_precip":     tot_p,
            "rainy_days":       rd,
            "total_days":       t,
            "rain_probability": p,
            "rain_percentage":  round(p * 100, 1),
            "prob_step":        f"P(Rain in {month_names[m-1]}) = {rd}/{t} = {round(p*100,1)}%",
        })

    # ── Yearly breakdown ───────────────────────────────────────
    years = sorted(set(r["year"] for r in records))
    yearly_summary = []
    for y in years:
        yr = [r for r in records if r["year"] == y]
        yt = [r["temp_mean"]     for r in yr]
        yp = [r["precipitation"] for r in yr]
        yrd = len([r for r in yr if r["precipitation"] >= 0.5])

        yearly_summary.append({
            "year":             y,
            "avg_temp":         round(float(np.mean(yt)), 2),
            "max_temp":         round(float(np.max(yt)), 1),
            "min_temp":         round(float(np.min(yt)), 1),
            "total_precip":     round(float(np.sum(yp)), 1),
            "rainy_days":       yrd,
            "total_days":       len(yr),
            "rain_probability": round(yrd / len(yr), 4),
        })

    # ── Step 4: Normal distribution fit ────────────────────────
    normal_dist = fit_normal_distribution(temps)

    # ── Step 5: Time-series regression & moving averages ───────
    x_days = list(range(len(temps)))
    daily_reg = perform_linear_regression(x_days, temps)

    x_years     = list(range(len(years)))
    y_year_avgs = [ys["avg_temp"] for ys in yearly_summary]
    yearly_reg  = perform_linear_regression(x_years, y_year_avgs)

    print(f"[REGRESSION] Daily:  {daily_reg['equation']}  R²={daily_reg['r_squared']}")
    print(f"[REGRESSION] Yearly: {yearly_reg['equation']}  R²={yearly_reg['r_squared']}")

    # Moving averages
    ma_7  = []
    ma_30 = []
    for i in range(len(temps)):
        if i >= 6:
            ma_7.append(round(float(np.mean(temps[i-6:i+1])), 2))
        else:
            ma_7.append(round(float(np.mean(temps[:i+1])), 2))

        if i >= 29:
            ma_30.append(round(float(np.mean(temps[i-29:i+1])), 2))
        else:
            ma_30.append(round(float(np.mean(temps[:i+1])), 2))

    trend_line = [round(daily_reg["slope"] * i + daily_reg["intercept"], 2) for i in x_days]

    # ── Step 6: Future predictions (purely statistical) ────────
    last_year = years[-1]
    slope     = yearly_reg["slope"]      # temperature change per year
    intercept = yearly_reg["intercept"]  # baseline

    avg_annual_precip = float(np.mean([ys["total_precip"] for ys in yearly_summary]))
    avg_annual_rainy  = int(round(float(np.mean([ys["rainy_days"] for ys in yearly_summary]))))

    # Precipitation trend regression
    yp_totals = [ys["total_precip"] for ys in yearly_summary]
    precip_reg = perform_linear_regression(x_years, yp_totals)

    future_predictions = []
    for idx in range(1, 6):
        future_x = len(years) - 1 + idx  # extrapolate from yearly regression
        pred_temp = round(slope * future_x + intercept, 2)
        pred_precip = round(precip_reg["slope"] * future_x + precip_reg["intercept"], 1)
        pred_year = last_year + idx

        # Heatwave risk = how far predicted temp is above historical mean
        temp_mean = temp_stats["mean"]
        temp_sd   = temp_stats["std_dev"] if temp_stats["std_dev"] > 0 else 1
        heat_z = (pred_temp - temp_mean) / temp_sd
        heat_prob = round(min(0.95, max(0.05, 0.15 + heat_z * 0.25)), 2)

        step_text = (
            f"y = {slope}·{future_x} + {intercept} = {pred_temp}°C  "
            f"(slope={slope}°C/year from regression)"
        )

        future_predictions.append({
            "year":                pred_year,
            "predicted_avg_temp":  pred_temp,
            "predicted_precip":    max(0, pred_precip),
            "predicted_rainy_days": avg_annual_rainy,
            "rain_probability":    round(avg_annual_rainy / 365.0, 4),
            "heatwave_probability": heat_prob,
            "step":                step_text,
        })

    print(f"[PREDICT] Future temps: {[fp['predicted_avg_temp'] for fp in future_predictions]}")

    # ── Build response ─────────────────────────────────────────
    return jsonify({
        "status": "success",
        "metadata": {
            "city":        city_name,
            "latitude":    lat,
            "longitude":   lon,
            "start_year":  start_year,
            "end_year":    end_year,
            "total_days":  total_days,
            "data_source": data_source,
        },
        "descriptive_stats": {
            "temperature":   temp_stats,
            "precipitation": precip_stats,
            "humidity":      humid_stats,
            "wind_speed":    wind_stats,
        },
        "probability_analysis": {
            "rain_probability":  rain_prob,
            "rain_percentage":   rain_pct,
            "total_rainy_days":  len(rainy_records),
            "total_dry_days":    dry_count,
            "prob_step":         prob_step,
            "intensity_counts": {
                "dry":      dry_count,
                "light":    light_count,
                "moderate": mod_count,
                "heavy":    heavy_count,
            },
        },
        "normal_distribution": normal_dist,
        "monthly_summary":     monthly_summary,
        "yearly_summary":      yearly_summary,
        "time_series": {
            "dates":           [r["date"] for r in records],
            "temps":           temps,
            "moving_avg_7":    ma_7,
            "moving_avg_30":   ma_30,
            "trend_line":      trend_line,
            "daily_regression":  daily_reg,
            "yearly_regression": yearly_reg,
        },
        "future_predictions":  future_predictions,
        "raw_records":         records,  # ALL records — no limit
    })


@app.route("/api/viva-guide", methods=["GET"])
def get_viva_guide():
    """Returns structured Viva Q&A with formulas and theory."""
    guide = {
        "title": "Weather Forecast Analysis Using Statistics and Probability",
        "concepts": [
            {
                "id": "mean",
                "name": "Mean (Average Temperature)",
                "formula": "\\bar{X} = \\frac{1}{N} \\sum_{i=1}^{N} X_i",
                "description": "The mean represents the arithmetic average of all temperature readings over the analysis period. It provides the central climate baseline against which individual days are compared.",
                "viva_q": "Why is Mean important in weather analysis?",
                "viva_a": "Mean gives us the standard climate benchmark for a city. If the daily temperature deviates significantly from the mean, we can identify unusual weather events like warm spells or cold waves.",
            },
            {
                "id": "median",
                "name": "Median (Middle Value)",
                "formula": "\\text{Median} = X_{\\frac{N+1}{2}} \\; (\\text{or avg of two middle values if N is even})",
                "description": "The median is the exact middle value when all temperature readings are sorted in ascending order. Unlike the mean, it is not affected by extreme outliers.",
                "viva_q": "When is Median better than Mean for weather data?",
                "viva_a": "When the dataset contains extreme heatwave days (e.g., 48°C) or unusually cold days, the Mean gets pulled toward that extreme. The Median remains at the true center and gives a more robust measure of typical weather.",
            },
            {
                "id": "mode",
                "name": "Mode (Most Frequent Temperature)",
                "formula": "\\text{Mode} = \\text{value with highest frequency } f(x)",
                "description": "The mode identifies which temperature value occurs most often in the dataset. For continuous weather data, values are rounded to 1 decimal place before finding mode.",
                "viva_q": "What does Mode tell us about weather?",
                "viva_a": "Mode tells us the most common temperature condition. If Hyderabad's mode is 30.0°C, it means 30°C is the most frequently experienced temperature, which is useful for building design, energy planning, etc.",
            },
            {
                "id": "variance",
                "name": "Variance (σ²)",
                "formula": "\\sigma^2 = \\frac{1}{N} \\sum_{i=1}^{N} (X_i - \\mu)^2",
                "description": "Variance measures the average of the squared deviations from the mean. It quantifies how spread out the temperature values are. A high variance means temperatures fluctuate widely.",
                "viva_q": "What does high variance in temperature data mean?",
                "viva_a": "High variance means the city experiences very different temperatures across the year — for example, Delhi has hot summers (45°C) and cold winters (5°C), giving high variance. Bengaluru with stable weather has low variance.",
            },
            {
                "id": "std_dev",
                "name": "Standard Deviation (σ)",
                "formula": "\\sigma = \\sqrt{\\sigma^2} = \\sqrt{\\frac{1}{N} \\sum (X_i - \\mu)^2}",
                "description": "Standard deviation is the square root of variance. It tells us in the same units (°C) how much temperature typically differs from the average.",
                "viva_q": "How do you interpret standard deviation in weather?",
                "viva_a": "If Mean = 30°C and σ = 3°C, most temperatures fall between 27°C and 33°C. A small σ means stable, predictable weather; a large σ means highly variable, unpredictable weather conditions.",
            },
            {
                "id": "probability",
                "name": "Rainfall Probability P(Rain)",
                "formula": "P(\\text{Rain}) = \\frac{\\text{Number of Rainy Days}}{\\text{Total Days Observed}}",
                "description": "Empirical probability of rainfall calculated from historical frequency. A day with precipitation ≥ 0.5mm is counted as a rainy day.",
                "viva_q": "How is historical probability used for future prediction?",
                "viva_a": "If 5 years of July data shows rain on 120 out of 155 days, then P(Rain in July) = 120/155 = 77.4%. This empirical probability helps farmers plan irrigation and travelers plan trips.",
            },
            {
                "id": "normal_dist",
                "name": "Normal (Gaussian) Distribution",
                "formula": "f(x) = \\frac{1}{\\sigma \\sqrt{2\\pi}} e^{-\\frac{1}{2}\\left(\\frac{x-\\mu}{\\sigma}\\right)^2}",
                "description": "Temperature data often follows a bell curve. The 68-95-99.7 empirical rule says 68% of data is within ±1σ, 95% within ±2σ, and 99.7% within ±3σ of the mean.",
                "viva_q": "What is the 68-95-99.7 rule in weather context?",
                "viva_a": "If μ=30°C and σ=3°C: 68% of days have temperatures between 27-33°C, 95% between 24-36°C. Any day outside ±2σ (below 24°C or above 36°C) is a statistical anomaly — possibly a heatwave or cold snap.",
            },
            {
                "id": "linear_regression",
                "name": "Linear Regression (Future Prediction)",
                "formula": "y = mx + c \\;, \\quad m = \\frac{N\\sum xy - \\sum x \\sum y}{N\\sum x^2 - (\\sum x)^2}",
                "description": "Linear regression finds the best-fit straight line through yearly average temperatures. The slope 'm' tells us how fast temperature is changing per year, and we extrapolate to predict future temperatures.",
                "viva_q": "How does your project predict next year's temperature?",
                "viva_a": "We compute yearly average temperatures (e.g., 2021→29°C, 2022→29.5°C, ...), fit a line y=mx+c using least squares, then plug in x for the future year. The slope m shows the warming/cooling trend per year.",
            },
        ],
        "viva_faq": [
            {
                "q": "What is the complete project workflow?",
                "a": "User selects city → Website sends request to Open-Meteo Historical Archive API → Gets 1-5 years of daily temperature, rainfall, humidity, wind data → Backend computes Mean, Median, Mode, Variance, Standard Deviation → Calculates rainfall probability → Fits Normal Distribution → Performs Linear Regression → Predicts future temperatures → Displays results in charts and tables.",
            },
            {
                "q": "Where does the weather data come from?",
                "a": "From the Open-Meteo Historical Archive API (https://archive-api.open-meteo.com/v1/archive). This is a free, open-source API that provides real historical weather records without needing any API key or registration.",
            },
            {
                "q": "Why don't you use a database?",
                "a": "Our project fetches data fresh from the API each time and computes all statistics on the fly in the backend. This ensures we always analyze the latest available data without maintaining a separate database.",
            },
            {
                "q": "Can statistics guarantee exact weather forecasts?",
                "a": "No. Weather is a chaotic, non-linear system. Statistical models give us high-probability estimates based on historical patterns. They identify trends and likelihoods, but cannot predict exact weather conditions with certainty.",
            },
            {
                "q": "What is the difference between population variance and sample variance?",
                "a": "Population variance divides by N (we use this since we have all the data for the period). Sample variance divides by N-1 and is used when working with a subset of data to get an unbiased estimate.",
            },
            {
                "q": "How do you handle missing data from the API?",
                "a": "If a day's mean temperature is missing but max and min are available, we compute mean as (max+min)/2. If temperature is completely missing, that day is skipped. For humidity and wind, reasonable defaults are used if null.",
            },
        ],
    }
    return jsonify({"status": "success", "guide": guide})


# ---------------------------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Weather Forecast Analysis Server")
    print("  Open-Meteo Historical API + Statistics Engine")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
