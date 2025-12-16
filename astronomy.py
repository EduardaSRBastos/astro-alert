from datetime import datetime, UTC
from skyfield.api import load, Topos
from skyfield import almanac, eclipselib
import numpy as np
from functools import lru_cache

# --- Global Skyfield setup with error handling ---
try:
    ts = load.timescale()
    eph = load("de421.bsp")
    earth, sun, moon = eph["earth"], eph["sun"], eph["moon"]
except Exception as e:
    print(f"[ERROR] Failed to load ephemeris data: {e}")
    ts = eph = earth = sun = moon = None

AU_KM = 149597870
SUN_RADIUS_KM = 696340
MOON_RADIUS_KM = 1737

METEOR_SHOWERS = [
    {
        "name": "Quadrantids",
        "peak": (1, 3),
        "start": (12, 28),
        "end": (1, 12),
        "hemisphere": "Northern",
        "best_time": "After midnight",
        "zhr": 120
    },
    {
        "name": "Lyrids",
        "peak": (4, 22),
        "start": (4, 16),
        "end": (4, 25),
        "hemisphere": "Both",
        "best_time": "Late night to dawn",
        "zhr": 18
    },
    {
        "name": "Perseids",
        "peak": (8, 12),
        "start": (7, 17),
        "end": (8, 24),
        "hemisphere": "Northern",
        "best_time": "After midnight",
        "zhr": 100
    },
    {
        "name": "Geminids",
        "peak": (12, 14),
        "start": (12, 4),
        "end": (12, 17),
        "hemisphere": "Both",
        "best_time": "All night",
        "zhr": 120
    }
]

def calculate_meteor_visibility(shower, hemisphere, moon_illum):
    visibility = 100
    if shower["hemisphere"] != "Both" and shower["hemisphere"] != hemisphere:
        visibility -= 60
    if moon_illum > 75:
        visibility -= 50
    elif moon_illum > 50:
        visibility -= 30
    elif moon_illum > 25:
        visibility -= 15
    return max(0, min(visibility, 100))

@lru_cache(maxsize=32)
def get_next_moon_phase(today=datetime.today().date()):
    phase_function = almanac.moon_phases(eph)
    mt0 = ts.utc(today.year, today.month, today.day)
    mt1 = ts.utc(today.year, today.month, today.day + 30)
    times, phases = almanac.find_discrete(mt0, mt1, phase_function)
    phase_names = {0: "New Moon", 1: "First Quarter", 2: "Full Moon", 3: "Last Quarter"}
    return phase_names[phases[0]], times[0].utc_datetime()

@lru_cache(maxsize=32)
def get_next_full_moon(today=datetime.today().date()):
    phase_function = almanac.moon_phases(eph)
    mt0 = ts.utc(today.year, today.month, today.day)
    mt1 = ts.utc(today.year, today.month, today.day + 30)
    times, phases = almanac.find_discrete(mt0, mt1, phase_function)
    for t, p in zip(times, phases):
        if p == 2:
            return t.utc_datetime()
    return None

@lru_cache(maxsize=32)
def get_upcoming_moon_phases(today=datetime.today().date()):
    phase_function = almanac.moon_phases(eph)
    mt0 = ts.utc(today.year, today.month, today.day)
    mt1 = ts.utc(today.year, today.month, today.day + 30)
    times, phases = almanac.find_discrete(mt0, mt1, phase_function)
    phase_names = {0: "New Moon", 1: "First Quarter", 2: "Full Moon", 3: "Last Quarter"}
    return [(phase_names[p], t.utc_datetime()) for t, p in zip(times, phases)]

@lru_cache(maxsize=32)
def get_next_eclipses(lat=0, lon=0, today=datetime.today().date()):
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)

    et0 = ts.utc(today.year, today.month, today.day)
    et1 = ts.utc(today.year + 5, 12, 31)

    t_lunar, y_lunar, _ = eclipselib.lunar_eclipses(et0, et1, eph)
    next_lunar_time, lunar_type = None, None
    for t_ecl, idx in zip(t_lunar, y_lunar):
        alt, _, _ = observer.at(t_ecl).observe(moon).apparent().altaz()
        if alt.degrees <= 0:
            continue
        next_lunar_time = t_ecl.utc_datetime()
        lunar_type = eclipselib.LUNAR_ECLIPSES[idx]
        break

    total_minutes = int((et1.utc_datetime() - et0.utc_datetime()).total_seconds() / 60)
    times_sun = ts.utc(today.year, today.month, today.day, 0, np.arange(0, total_minutes, 10))
    sun_app = observer.at(times_sun).observe(sun).apparent()
    moon_app = observer.at(times_sun).observe(moon).apparent()

    separation = sun_app.separation_from(moon_app).degrees
    sun_radius = np.degrees(np.arcsin(SUN_RADIUS_KM / (sun_app.distance().au * AU_KM)))
    moon_radius = np.degrees(np.arcsin(MOON_RADIUS_KM / (moon_app.distance().au * AU_KM)))

    indices = np.where(separation < (sun_radius + moon_radius))[0]
    solar_type, next_solar_time = None, None

    if indices.size:
        i = indices[0]
        if moon_radius[i] >= sun_radius[i]:
            solar_type = "Total"
        else:
            solar_type = "Annular"
        next_solar_time = times_sun[i].utc_datetime()

    return (solar_type, next_solar_time), (lunar_type, next_lunar_time)

def get_next_meteor_shower():
    today = datetime.now(UTC).date()
    candidates = []

    for shower in METEOR_SHOWERS:
        start = datetime(today.year, *shower["start"], tzinfo=UTC)
        end = datetime(today.year, *shower["end"], tzinfo=UTC)
        peak = datetime(today.year, *shower["peak"], tzinfo=UTC)

        if end < datetime.now(UTC):
            start = start.replace(year=today.year + 1)
            end = end.replace(year=today.year + 1)
            peak = peak.replace(year=today.year + 1)

        candidates.append((peak, start, end, shower))

    candidates.sort(key=lambda x: x[0])
    peak, start, end, shower = candidates[0]
    return shower, start, end, peak
