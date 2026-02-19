import streamlit as st
import pandas as pd

# ---------- LOAD DATA FROM CSV (STABLE FOR DEPLOYMENT) ----------
@st.cache_data
def load_data():
    pilots = pd.read_csv("pilot_roster.csv")
    drones = pd.read_csv("drone_fleet.csv")
    missions = pd.read_csv("missions.csv")
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

        if pilot.get("current_assignment", "") != "":
            warnings.append("⚠️ Pilot already assigned (double booking risk)")

    if drone is not None:
        if drone.get("status", "").lower() == "maintenance":
            warnings.append("⚠️ Drone under maintenance")

    if not warnings:
        return ["✅ No conflicts detected"]

    return warnings


# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Skylark Drone AI Agent", layout="wide")

st.title("🚁 Skylark Drone Operations Coordinator AI Agent")
st.write("AI Agent for Pilot Assignment, Drone Inventory & Conflict Detection")

# Load CSV data
pilots, drones, missions = load_data()

# ---------- MISSION SELECTION ----------
st.subheader("🎯 Mission Assignment")

mission_ids = missions["project_id"].tolist()
selected_mission_id = st.selectbox("Select Mission", mission_ids)

mission = missions[missions["project_id"] == selected_mission_id].iloc[0]

if st.button("🤖 Assign Best Pilot & Drone"):
    pilot = match_pilot(mission, pilots)
    drone = match_drone(mission, drones)
    conflicts = detect_conflicts(pilot, drone, mission)

    st.subheader("📋 Assignment Result")

    col1, col2 = st.columns(2)

    with col1:
        if pilot is not None:
            st.success(f"👨‍✈️ Assigned Pilot: {pilot['name']}")
            st.write(f"📍 Location: {pilot.get('location', 'N/A')}")
            st.write(f"🛠 Skills: {pilot['skills']}")
        else:
            st.error("No suitable pilot found")

    with col2:
        if drone is not None:
            st.success(f"🚁 Assigned Drone: {drone['drone_id']}")
            st.write(f"⚙️ Capabilities: {drone['capabilities']}")
        else:
            st.error("No suitable drone available")

    st.subheader("⚠️ Conflict Analysis")
    for warning in conflicts:
        st.warning(warning)

# ---------- DASHBOARD ----------
st.subheader("👨‍✈️ Pilot Roster")
st.dataframe(pilots, use_container_width=True)

st.subheader("🚁 Drone Fleet")
st.dataframe(drones, use_container_width=True)

st.subheader("📁 Missions")
st.dataframe(missions, use_container_width=True)
