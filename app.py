import streamlit as st
import pandas as pd
import gspread
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------- GOOGLE SHEETS CONNECTION ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ---------- GOOGLE SHEETS CONNECTION (STREAMLIT SECRETS VERSION) ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets (NOT credentials.json)
creds_dict = st.secrets["gcp_service_account"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 🔁 Replace with your EXACT sheet file names
pilot_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1PFX9Vg4MWkjG5PaqXfxRdaNWoRor6jmHmwKBZjUlwqU/edit?gid=1010487325#gid=1010487325").sheet1
drone_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/14mCwUviXDlXcJl1_zUvu0i9SRcYhkoJ_rBjq15to2aE/edit?gid=646567280#gid=646567280").sheet1
mission_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1rqMJ86YV5G4WXTuXwo1AA8N-iNvL_NDdzV4AcOYQUCw/edit?gid=550071242#gid=550071242").sheet1


# ---------- LOAD DATA ----------
def load_data():
    pilots = pd.DataFrame(pilot_sheet.get_all_records())
    drones = pd.DataFrame(drone_sheet.get_all_records())
    missions = pd.DataFrame(mission_sheet.get_all_records())
    return pilots, drones, missions

# ---------- PILOT MATCHING ----------
def match_pilot(mission, pilots):
    available = pilots[pilots["status"] == "Available"]
    
    skilled = available[
        available["skills"].str.contains(mission["required_skills"], na=False, case=False)
    ]

    if not skilled.empty:
        return skilled.iloc[0]
    return None

# ---------- DRONE MATCHING (Weather Check) ----------
def match_drone(mission, drones):
    available = drones[drones["status"] == "Available"]

    if mission["weather"] == "Rainy":
        suitable = available[
            available["capabilities"].str.contains("IP", na=False)
        ]
    else:
        suitable = available

    if not suitable.empty:
        return suitable.iloc[0]
    return None

# ---------- CONFLICT DETECTION ----------
def detect_conflicts(pilot, mission, pilots):
    if pilot is None:
        return "No pilot available"

    if pilot["current_assignment"] != "":
        return "⚠️ Double booking detected!"

    if mission["required_skills"].lower() not in pilot["skills"].lower():
        return "⚠️ Skill mismatch warning!"

    return "✅ No conflicts"

# ---------- STREAMLIT UI ----------
st.title("🚁 Skylark Drone Operations Coordinator AI Agent")

st.write("AI Agent for Pilot Assignment, Drone Tracking & Conflict Detection")

pilots, drones, missions = load_data()

# Mission Selection
mission_ids = missions["project_id"].tolist()
selected_mission_id = st.selectbox("Select Mission", mission_ids)

mission = missions[missions["project_id"] == selected_mission_id].iloc[0]

if st.button("🤖 Assign Best Pilot & Drone"):
    pilot = match_pilot(mission, pilots)
    drone = match_drone(mission, drones)

    conflict_msg = detect_conflicts(pilot, mission, pilots)

    st.subheader("📋 Assignment Result")

    if pilot is not None:
        st.success(f"👨‍✈️ Assigned Pilot: {pilot['name']}")
    else:
        st.error("No suitable pilot found")

    if drone is not None:
        st.success(f"🚁 Assigned Drone: {drone['drone_id']}")
    else:
        st.error("No suitable drone available")

    st.warning(conflict_msg)

# Dashboard Tables
st.subheader("👨‍✈️ Pilot Roster")
st.dataframe(pilots)

st.subheader("🚁 Drone Fleet")
st.dataframe(drones)

st.subheader("📁 Missions")
st.dataframe(missions)



