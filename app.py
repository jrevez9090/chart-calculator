import streamlit as st
import swisseph as swe
import datetime
import pytz
import re
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

# =========================
# SWISS EPHEMERIS SETUP
# =========================

swe.set_ephe_path('./ephe')

st.set_page_config(page_title="Natal Chart Calculator", layout="centered")

st.title("Natal Chart Calculator (Solar Fire Clone Mode)")
st.markdown("Enter birth data to calculate planetary positions.")

# =========================
# INPUTS
# =========================

date = st.date_input(
    "Birth Date",
    value=datetime.date(1980,1,1),
    min_value=datetime.date(1500,1,1),
    max_value=datetime.date(2100,12,31)
)

time_text = st.text_input("Birth Time (format: 00h00m)")
place = st.text_input("Birth Place (City, Country)")

# Solar Fire aligned Delta-T
delta_t_seconds = 63

# =========================
# HELPERS
# =========================

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

def format_position(longitude):
    signs = [
        "Aries","Taurus","Gemini","Cancer",
        "Leo","Virgo","Libra","Scorpio",
        "Sagittarius","Capricorn","Aquarius","Pisces"
    ]
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    degree = int(longitude % 30)
    minutes_full = (longitude % 30 - degree) * 60
    minutes = int(minutes_full)
    seconds = int((minutes_full - minutes) * 60)
    return f"{degree}º{minutes:02d}'{seconds:02d}\" {signs[sign_index]}"

# =========================
# CALCULATE
# =========================

if st.button("Calculate"):

    time_obj = parse_time(time_text)

    if not place:
        st.error("Please enter a location.")
        st.stop()

    if time_obj is None:
        st.error("Please enter time in format 00h00m.")
        st.stop()

    # ---------------------
    # GEO (ROBUST)
    # ---------------------

    geolocator = Nominatim(user_agent="astro_app_joana_revez_2026")

    location = None

    for attempt in range(3):
        try:
            location = geolocator.geocode(place, timeout=10)
            if location:
                break
            time.sleep(1)
        except (GeocoderTimedOut, GeocoderServiceError):
            time.sleep(1)

    if not location:
        st.error("City lookup temporarily unavailable. Please try again.")
        st.stop()

    lat = location.latitude
    lon = location.longitude

    # ---------------------
    # TIMEZONE
    # ---------------------

    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)

    if timezone_str is None:
        st.error("Timezone not found.")
        st.stop()

    timezone = pytz.timezone(timezone_str)

    local_dt = datetime.datetime.combine(date, time_obj)
    local_dt = timezone.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    st.markdown("### Technical Data")
    st.write("UTC used:", utc_dt)

    # ---------------------
    # JULIAN DAY
    # ---------------------

    jd_ut = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600
    )

    delta_t_days = delta_t_seconds / 86400
    jd_et = jd_ut + delta_t_days  # mantido para Solar Fire alignment

    st.write("Julian Day UT:", jd_ut)

    # ---------------------
    # PLANETS
    # ---------------------

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN
    }

    st.markdown("### Planetary Positions")

    planet_positions = {}

    for name, body in planets.items():
        pos = swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH)
        longitude = pos[0][0]
        planet_positions[name] = longitude
        st.write(f"{name} — {format_position(longitude)}")

    # ---------------------
    # HOUSES (ALCABITIUS)
    # ---------------------

    houses, ascmc = swe.houses_ex(
        jd_ut,
        lat,
        lon,
        b'A',
        swe.FLG_SWIEPH
    )

    st.markdown("### House Cusps (Alcabitius)")
    for i in range(12):
        st.write(f"House {i+1} — {format_position(houses[i])}")

    asc = ascmc[0]
    mc = ascmc[1]
    desc = (asc + 180) % 360
    ic = (mc + 180) % 360

    st.markdown("### Angles (Alcabitius)")
    st.write("Ascendant —", format_position(asc))
    st.write("MC —", format_position(mc))
    st.write("Descendant —", format_position(desc))
    st.write("IC —", format_position(ic))

    # ---------------------
    # SECT
    # ---------------------

    sun_long = planet_positions["Sun"]
    is_day = ((sun_long - desc) % 360) < 180

    st.markdown("### Sect")
    st.write("Day Chart" if is_day else "Night Chart")

    st.write("Latitude usada:", lat)
    st.write("Longitude usada:", lon)
    
    # ---------------------
    # LOTS
    # ---------------------

    moon_long = planet_positions["Moon"]

    if is_day:
        fortune = (asc + moon_long - sun_long) % 360
        daimon = (asc + sun_long - moon_long) % 360
    else:
        fortune = (asc + sun_long - moon_long) % 360
        daimon = (asc + moon_long - sun_long) % 360

    st.markdown("### Lots")
    st.write("Lot of Fortune —", format_position(fortune))
    st.write("Lot of Daimon —", format_position(daimon))
