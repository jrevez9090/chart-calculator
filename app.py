import streamlit as st
import swisseph as swe
import datetime
import pytz
import re
from timezonefinder import TimezoneFinder

# =========================
# SWISS EPHEMERIS
# =========================

swe.set_ephe_path('./ephe')

st.set_page_config(page_title="Natal Chart Calculator", layout="centered")
st.title("Natal Chart Calculator (Alcabitius Correct)")

# =========================
# INPUTS
# =========================

date = st.date_input(
    "Birth Date",
    value=datetime.date(1980, 1, 1),
    min_value=datetime.date(1500, 1, 1),
    max_value=datetime.date(2100, 12, 31)
)

time_text = st.text_input("Birth Time (format: 00h00m)")

lat = st.number_input("Latitude", value=0.0, format="%.6f")
lon = st.number_input("Longitude", value=0.0, format="%.6f")

timezone_str = st.text_input("Timezone (e.g. Europe/Lisbon)")

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

def get_house(longitude, houses):
    for i in range(12):
        cusp_start = houses[i]
        cusp_end = houses[(i+1) % 12]

        if cusp_start < cusp_end:
            if cusp_start <= longitude < cusp_end:
                return i+1
        else:
            if longitude >= cusp_start or longitude < cusp_end:
                return i+1
    return None

# =========================
# CALCULATE
# =========================

if st.button("Calculate"):

    time = parse_time(time_text)

    if time is None:
        st.error("Please enter time in format 00h00m.")
        st.stop()

    if not timezone_str:
        st.error("Please enter timezone.")
        st.stop()

    timezone = pytz.timezone(timezone_str)

    local_dt = datetime.datetime.combine(date, time)
    local_dt = timezone.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    jd_ut = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600
    )

    # DEBUG (podes apagar depois)
    st.write("UTC used:", utc_dt)
    st.write("Latitude:", lat)
    st.write("Longitude:", lon)

    # =====================
    # HOUSES — ALCABITIUS REAL
    # =====================

    houses, ascmc = swe.houses_ex(
        jd_ut,
        lat,
        lon,
        b'A',
        swe.FLG_SWIEPH
    )

    asc = ascmc[0]
    mc = ascmc[1]
    desc = (asc + 180) % 360
    ic = (mc + 180) % 360

    st.markdown("### House Cusps (Alcabitius)")
    for i in range(12):
        st.write(f"House {i+1} — {format_position(houses[i])}")

    st.markdown("### Angles")
    st.write("Ascendant —", format_position(asc))
    st.write("MC —", format_position(mc))
    st.write("Descendant —", format_position(desc))
    st.write("IC —", format_position(ic))

    # =====================
    # PLANETS
    # =====================

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN
    }

    planet_positions = {}

    st.markdown("### Planetary Positions")

    for name, body in planets.items():
        pos = swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH)
        longitude = pos[0][0]
        planet_positions[name] = longitude

        house = get_house(longitude, houses)

        st.write(f"{name} — {format_position(longitude)} — House {house}")

    # =====================
    # SECT
    # =====================

    sun_long = planet_positions["Sun"]
    is_day = ((sun_long - desc) % 360) < 180

    st.markdown("### Sect")
    st.write("Day Chart" if is_day else "Night Chart")

    # =====================
    # LOTS
    # =====================

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
