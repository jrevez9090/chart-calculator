import streamlit as st
import swisseph as swe
import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Natal Chart Calculator", layout="centered")

st.title("Natal Chart Calculator")

st.markdown("Enter birth data to calculate planetary positions.")

# ------------------------
# INPUTS
# ------------------------

date = st.date_input(
    "Birth Date",
    value=datetime.date(1980,1,1),
    min_value=datetime.date(1500,1,1),
    max_value=datetime.date(2100,12,31)
)

time_text = st.text_input("Birth Time (format: 00h00m)")

place = st.text_input("Birth Place (City, Country)")

# ------------------------
# TIME PARSER
# ------------------------

def parse_time(text):
    if not text:
        return None
    
    text = text.strip().lower().replace(" ", "")
    match = re.fullmatch(r"(\d{1,2})h(\d{1,2})m", text)

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return datetime.time(hour, minute)

    return None


# ------------------------
# CALCULATE
# ------------------------

if st.button("Calculate"):

    time = parse_time(time_text)

    if not place:
        st.error("Please enter a location.")
        st.stop()

    if time is None:
        st.error("Please enter time in format 00h00m (example: 04h35m).")
        st.stop()

    # Geocode location
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place)

    if not location:
        st.error("Location not found.")
        st.stop()

    lat = location.latitude
    lon = location.longitude

    # Find timezone
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)

    if timezone_str is None:
        st.error("Timezone could not be determined.")
        st.stop()

    timezone = pytz.timezone(timezone_str)

    # Local datetime
    local_dt = datetime.datetime.combine(date, time)
    local_dt = timezone.localize(local_dt)

    # Convert to UTC
    utc_dt = local_dt.astimezone(pytz.utc)

    # Julian Day
    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60
    )

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN
    }

    signs = [
        "Aries","Taurus","Gemini","Cancer",
        "Leo","Virgo","Libra","Scorpio",
        "Sagittarius","Capricorn","Aquarius","Pisces"
    ]

    st.markdown("### Planetary Positions")

    for name, body in planets.items():
        position = swe.calc_ut(jd, body)
        longitude = position[0][0]

        sign_index = int(longitude // 30)
        degree = int(longitude % 30)
        minutes = int(((longitude % 30) - degree) * 60)

        st.write(f"{name} — {degree}º{minutes:02d}' {signs[sign_index]}")
