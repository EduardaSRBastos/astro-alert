from datetime import datetime
import requests

today = datetime.today()

# Moon phases
moon_data = requests.get(f'https://aa.usno.navy.mil/api/moon/phases/date?date={today.strftime("%Y-%m-%d")}&nump=4').json()
phases = moon_data["phasedata"]

# Print 4 upcoming phases
print("Upcoming Moon Phases:")

for p in phases:
    print(f"{p['phase']} - {p['day']:02d}/{p['month']:02d}/{p['year']}")

# Next phase
print("\n")
print(f"Next Moon Phase: {phases[0]['phase']} - {phases[0]['day']:02d}/{phases[0]['month']:02d}/{phases[0]['year']}")

# Next full moon
full_moon = next((p for p in phases if p['phase'] == "Full Moon"), None)

print("\n")
if full_moon:
    print(f"Next Full Moon: {full_moon['day']:02d}/{full_moon['month']:02d}/{full_moon['year']}")


# Solar eclipses
ip_data = requests.get("https://ipapi.co/json/").json()

lat = ip_data["latitude"]
lon = ip_data["longitude"]
loc = ip_data["region"]

def get_next_visible_eclipse(year, lat, lon):
  for y in (year, year + 1):
    eclipses = requests.get(
      f'https://aa.usno.navy.mil/api/eclipses/solar/year?year={y}').json()["eclipses_in_year"]
    
    for e in eclipses:
      eclipse_date = datetime(int(e["year"]), int(e["month"]), int(e["day"]))
      
      if eclipse_date >= today:
        eclipse_location = requests.get(
          f'https://aa.usno.navy.mil/api/eclipses/solar/date?date={eclipse_date.strftime("%Y-%m-%d")}&coords={lat},{lon}&height=0').json()

        if "error" not in eclipse_location:
          return eclipse_location, eclipse_date

  return None, None

next_eclipse, eclipse_date = get_next_visible_eclipse(today.year, lat, lon)

next_eclipse_data = next_eclipse["properties"]
eclipse_type = next_eclipse_data["description"].split("in")[1].split("at")[0].strip()
eclipse_date = f"{next_eclipse_data['day']:02d}/{next_eclipse_data['month']:02d}/{next_eclipse_data['year']}"

print("\n")
print(f"Next Solar Eclipse in {loc}: {eclipse_type} - {eclipse_date}")
