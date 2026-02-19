import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------- GOOGLE SHEETS CONNECTION (STREAMLIT SECRETS FINAL) ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]


# Load credentials from Streamlit Secrets (TOML format)
creds_dict = st.secrets["gcp_service_account"]

# Fix newline issue in private key (VERY IMPORTANT)
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

# Authorize client
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ---------- OPEN GOOGLE SHEETS (USE CLEAN URL ONLY) ----------
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


# ---------- ROSTER MANAGEMENT ----------
def update_pilot_status(pilot_name, new_status):
    records = pilot_sheet.get_all_records()
    for i, record in enumerate(records, start=2):  # Start from row 2 (skip header)
        if record["name"] == pilot_name:
            pilot_sheet.update_cell(i, 6, new_status)  # status column
            return True
    return False


# ---------- PILOT MATCHING ----------
def match_pilot(mission, pilots):
    available = pilots[pilots["status"].str.lower() == "available"]

    # Skill match
    skilled = available[
        available["skills"].str.contains(
            str(mission["required_skills"]), na=False, case=False
        )
    ]

    # Location match (bonus)
    if "location" in pilots.columns and "location" in mission:
        skilled = skilled.sort_values(by="location")

    if not skilled.empty:
        return skilled.iloc[0]

    return None


# ---------- DRONE MATCHING (WEATHER COMPATIBILITY) ----------
def match_drone(mission, drones):
    available = drones[drones["status"].str.lower() == "available"]

    weather = str(mission.get("weather", "")).lower()

    # If rainy, require IP rated drones
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
        if pilot.get("current_assignment"):
            warnings.append("⚠️ Pilot double booking risk")

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


# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Skylark Drone AI Agent", layout="wide")

st.title("🚁 Skylark Drone Operations Coordinator AI Agent")
st.markdown(
    "AI Agent for **Pilot Assignment, Drone Inventory, Conflict Detection & Google Sheets Sync**"
)

# Load data
pilots, drones, missions = load_data()

# ---------- MISSION SELECTION ----------
st.subheader("🎯 Mission Assignment")

if not missions.empty:
    mission_ids = missions["project_id"].tolist()
    selected_mission_id = st.selectbox("Select Mission", mission_ids)

    mission = missions[missions["project_id"] == selected_mission_id].iloc[0]

    if st.button("🤖 Assign Best Pilot & Drone", use_container_width=True):
        pilot = match_pilot(mission, pilots)
        drone = match_drone(mission, drones)
        conflicts = detect_conflicts(pilot, drone, mission)

        st.subheader("📋 Assignment Result")

        col1, col2 = st.columns(2)

        with col1:
            if pilot is not None:
                st.success(f"👨‍✈️ Assigned Pilot: {pilot['name']}")
                st.write(f"📍 Location: {pilot['location']}")
                st.write(f"🛠 Skills: {pilot['skills']}")
            else:
                st.error("No suitable pilot found")

        with col2:
            if drone is not None:
                st.success(f"🚁 Assigned Drone: {drone['drone_id']}")
                st.write(f"📍 Location: {drone['location']}")
                st.write(f"⚙️ Capabilities: {drone['capabilities']}")
            else:
                st.error("No suitable drone available")

        st.subheader("⚠️ Conflict & Risk Analysis")
        for warning in conflicts:
            st.warning(warning)

# ---------- ROSTER MANAGEMENT ----------
st.subheader("👨‍✈️ Pilot Roster Management")

pilot_names = pilots["name"].tolist()
selected_pilot = st.selectbox("Select Pilot to Update Status", pilot_names)
new_status = st.selectbox("New Status", ["Available", "On Leave", "Unavailable"])

if st.button("🔄 Update Pilot Status (Sync to Google Sheets)"):
    success = update_pilot_status(selected_pilot, new_status)
    if success:
        st.success("Pilot status updated & synced to Google Sheets!")
        st.cache_data.clear()
    else:
        st.error("Failed to update pilot status")

# ---------- DASHBOARD TABLES ----------
st.subheader("📊 Live Operations Dashboard")

tab1, tab2, tab3 = st.tabs(["👨‍✈️ Pilot Roster", "🚁 Drone Fleet", "📁 Missions"])

with tab1:
    st.dataframe(pilots, use_container_width=True)

with tab2:
    st.dataframe(drones, use_container_width=True)

with tab3:
    st.dataframe(missions, use_container_width=True)


