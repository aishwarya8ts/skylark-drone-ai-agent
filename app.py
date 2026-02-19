import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- GOOGLE SHEETS CONNECTION (STABLE & SIMPLE) ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Use credentials.json directly (MOST STABLE FOR STREAMLIT CLOUD)
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)
client = gspread.authorize(creds)

# ---------- OPEN GOOGLE SHEETS ----------
pilot_sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1PFX9Vg4MWkjG5PaqXfxRdaNWoRor6jmHmwKBZjUlwqU"
).sheet1

drone_sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/14mCwUviXDlXcJl1_zUvu0i9SRcYhkoJ_rBjq15to2aE"
).sheet1

mission_sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1rqMJ86YV5G4WXTuXwo1AA8N-iNvL_NDdzV4AcOYQUCw"
).sheet1


# ---------- LOAD DATA ----------
@st.cache_data(ttl=60)
def load_data():
    pilots = pd.DataFrame(pilot_sheet.get_all_records())
    drones = pd.DataFrame(drone_sheet.get_all_records())
    missions = pd.DataFrame(mission_sheet.get_all_records())
    return pilots, drones, missions


# ---------- PILOT MATCHING ----------
def match_pilot(mission, pilots):
    available = pilots[pilots["status"].str.lower() == "available"]

    skilled = available[
        available["skills"].str.contains(
            str(mission["required_skills"]), na=False, case=False
        )
    ]

    if not skilled.empty:
        return skilled.iloc[0]
    return None


# ---------- DRONE MATCHING ----------
def match_drone(mission, drones):
    available = drones[drones["status"].str.lower() == "available"]

    weather = str(mission.get("weather", "")).lower()

    if "rain" in weather:
        suitable = available[
            available["capabilities"].str.contains("IP", na=False, case=False)
        ]
    else:
        suitable = available

    if not suitable.empty:
        return suitable.iloc[0]
    return None


# ---------- CONFLICT DETECTION ----------
def detect_conflicts(pilot, drone, mission):
    warnings = []

    if pilot is None:
        warnings.append("❌ No pilot available")

    if drone is None:
        warnings.append("❌ No drone available")

    if pilot is not None:
        if str(mission["required_skills"]).lower() not in str(pilot["skills"]).lower():
            warnings.append("⚠️ Skill mismatch warning")

    if drone is not None:
        if drone.get("status", "").lower() == "maintenance":
            warnings.append("⚠️ Drone under maintenance")

        weather = str(mission.get("weather", "")).lower()
        if "rain" in weather and "ip" not in str(drone["capabilities"]).lower():
            warnings.append("⚠️ Weather risk: Non-waterproof drone")

    if not warnings:
        return ["✅ No conflicts detected"]

    return warnings


# ---------- UI ----------
st.set_page_config(page_title="Skylark Drone AI Agent", layout="wide")

st.title("🚁 Skylark Drone Operations Coordinator AI Agent")

pilots, drones, missions = load_data()

st.subheader("🎯 Mission Assignment")

if not missions.empty:
    mission_ids = missions["project_id"].tolist()
    selected_mission_id = st.selectbox("Select Mission", mission_ids)

    mission = missions[missions["project_id"] == selected_mission_id].iloc[0]

    if st.button("🤖 Assign Best Pilot & Drone"):
        pilot = match_pilot(mission, pilots)
        drone = match_drone(mission, drones)
        conflicts = detect_conflicts(pilot, drone, mission)

        st.subheader("📋 Assignment Result")

        if pilot is not None:
            st.success(f"👨‍✈️ Assigned Pilot: {pilot['name']}")
        else:
            st.error("No suitable pilot found")

        if drone is not None:
            st.success(f"🚁 Assigned Drone: {drone['drone_id']}")
        else:
            st.error("No suitable drone available")

        for warning in conflicts:
            st.warning(warning)

st.subheader("👨‍✈️ Pilot Roster")
st.dataframe(pilots, use_container_width=True)

st.subheader("🚁 Drone Fleet")
st.dataframe(drones, use_container_width=True)

st.subheader("📁 Missions")
st.dataframe(missions, use_container_width=True)
