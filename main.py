from datetime import datetime, timedelta
from skyfield.api import load, Topos
from skyfield import almanac, eclipselib
import requests
import numpy as np

# Today
today = datetime.today()

# Location and timezone
ip_data = requests.get("https://ipapi.co/json/").json()
lat, lon = ip_data["latitude"], ip_data["longitude"]
loc = ip_data["region"]
offset_str = ip_data["utc_offset"]
offset = timedelta(
    hours=int(offset_str[1:3]), 
    minutes=int(offset_str[3:])
)
if offset_str[0] == "-":
    offset = -offset

# Skyfield setup
ts = load.timescale()
eph = load('de421.bsp')
earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)

# Constants
AU_KM = 149597870
SUN_RADIUS_KM = 696340
MOON_RADIUS_KM = 1737
EARTH_RADIUS_KM = 6371

# Moon Phases
phase_function = almanac.moon_phases(eph)
mt0 = ts.utc(today.year, today.month, today.day)
mt1 = ts.utc(today.year, today.month, today.day + 30)
times, phases = almanac.find_discrete(mt0, mt1, phase_function)
phase_names = {0: "New Moon", 1: "First Quarter", 2: "Full Moon", 3: "Last Quarter"}

print("Upcoming Moon Phases:")
for t, phase in zip(times, phases):
    dt = t.utc_datetime()
    print(f"{phase_names[phase]} - {dt.day:02d}/{dt.month:02d}/{dt.year}")
    if phase == 2:
        next_full_moon = t.utc_datetime()

# Next Moon Phase
next_phase_t, next_phase_index = times[0], phases[0]
next_phase_name = phase_names[next_phase_index]
print(f"\nNext Moon Phase:\n{next_phase_name} - {next_phase_t.utc_datetime().day:02d}/{next_phase_t.utc_datetime().month:02d}/{next_phase_t.utc_datetime().year}")

# Next Full Moon
print(f"\nNext Full Moon: {next_full_moon.day:02d}/{next_full_moon.month:02d}/{next_full_moon.year}")

# Next Solar Eclipse
et0 = ts.utc(today.year, today.month, today.day)
et1 = ts.utc(today.year + 5, 12, 31)
total_minutes = int((et1.utc_datetime() - et0.utc_datetime()).total_seconds() / 60)
times_sun = ts.utc(today.year, today.month, today.day, 0, np.arange(0, total_minutes, 10))

sun_app = observer.at(times_sun).observe(sun).apparent()
moon_app = observer.at(times_sun).observe(moon).apparent()
separation = sun_app.separation_from(moon_app).degrees
sun_radius = np.degrees(np.arcsin(SUN_RADIUS_KM / (sun_app.distance().au * AU_KM)))
moon_radius = np.degrees(np.arcsin(MOON_RADIUS_KM / (moon_app.distance().au * AU_KM)))

indices = np.where(separation < (sun_radius + moon_radius))[0] 
if indices.size > 0:
    t_next = times_sun[indices[0]].utc_datetime() + offset
    sep = separation[indices[0]]
    sr, mr = sun_radius[indices[0]], moon_radius[indices[0]]
    if mr >= sr and sep < sr:
        eclipse_type = "Total"
    elif mr < sr and sep < sr:
        eclipse_type = "Annular"
    else:
        eclipse_type = "Partial"
    print(f"\nNext Solar Eclipse in {loc}:\n{eclipse_type} - {t_next.strftime('%d/%m/%Y - %H:%M')}")
else:
    print(f"\nNo visible solar eclipses in the next 5 years for {loc}.")

# Next Lunar Eclipse
t_lunar, y_lunar, details = eclipselib.lunar_eclipses(et0, et1, eph)
next_lunar_time, lunar_type = None, None
for t_ecl, idx in zip(t_lunar, y_lunar):
    alt, az, dist = observer.at(t_ecl).observe(moon).apparent().altaz()
    if alt.degrees <= 0:
        continue
    next_lunar_time = t_ecl.utc_datetime() + offset
    lunar_type = eclipselib.LUNAR_ECLIPSES[idx]
    break

if next_lunar_time:
    print(f"\nNext Lunar Eclipse in {loc}:\n{lunar_type} - {next_lunar_time.strftime('%d/%m/%Y - %H:%M')}")
else:
    print(f"\nNo visible lunar eclipses in the next 5 years for {loc}.")
