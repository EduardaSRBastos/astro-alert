import os, json, requests
from datetime import timedelta
import numpy as np
from skyfield import almanac
from astronomy import ts, eph

cached_location = None

def get_location():
    global cached_location
    if cached_location:
        return cached_location

    lat = lon = 0
    loc = "Unknown"
    offset_str = "+0000"
    loc_data = os.getenv("MY_LOCATION")

    if loc_data:
        try:
            data = json.loads(loc_data)
            lat = data.get("latitude", 0)
            lon = data.get("longitude", 0)
            loc = data.get("region", "Unknown")
            offset_str = data.get("utc_offset", "+0000")
        except Exception as e:
            print(f"[WARN] Could not load location from secret: {e}")
    else:
        try:
            ip_data = requests.get("https://ipapi.co/json/").json()
            lat = ip_data.get("latitude", 0)
            lon = ip_data.get("longitude", 0)
            loc = ip_data.get("region", "Unknown")
            offset_str = ip_data.get("utc_offset", "+0000")
        except Exception as e:
            print(f"[WARN] Could not fetch location: {e}")

    try:
        offset = timedelta(hours=int(offset_str[1:3]), minutes=int(offset_str[3:]))
        if offset_str[0] == "-":
            offset = -offset
    except Exception as e:
        print(f"[WARN] Could not parse offset: {e}")
        offset = timedelta(0)

    cached_location = (lat, lon, loc, offset)
    return cached_location

def get_hemisphere(lat: float):
    if lat > 0:
        return "Northern"
    elif lat < 0:
        return "Southern"
    return "Both"

def get_moon_illumination(time):
    t = ts.from_datetime(time)
    phase_angle = almanac.moon_phase(eph, t).degrees
    illumination = (1 + np.cos(np.radians(phase_angle))) / 2
    return int(illumination * 100)
