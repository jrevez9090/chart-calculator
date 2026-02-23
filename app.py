import streamlit as st
import swisseph as swe
import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Natal Chart Calculator", layout="centered")

st.title("Natal Chart Calculator")

st.markdown("Enter birth data to calculate planetary positions.")

# ------------------------
# INPUTS
# ------------------------

date = st.date_input("Birth Date")
time = st.time_input("Birth Time")
place = st.text_input("Birth Place (City, Country)")

# ------------------------
# CALCULATE
# ------------------------

if st.button("Calculate"):

    if not place:
        st.error("Please enter a location.")
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
        utc_dt.hour + utc_dt.minute/60
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
        minutes = int((longitude % 1) * 60)

        st.write(f"{name} — {degree}º{minutes}' {signs[sign_index]}")
