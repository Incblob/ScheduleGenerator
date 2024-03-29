import streamlit as st
import numpy as np
from modules.ui_screens import ui_csv_import, ui_actors, ui_scenes, ui_schedule

import logging

logging.basicConfig(level=logging.INFO)

logging.debug("initializing session states")
# Initialize streamlit session states
def check_and_init_session_state(state):
    if state not in st.session_state:
        st.session_state[state] = []

for state in ["actors", "requirements", "dates", "indexes", "date_range"]:
    check_and_init_session_state(state)

if "np_availabilities" not in st.session_state:
    st.session_state["np_availabilities"] = np.array([])
if "active_scenes" not in st.session_state:
    st.session_state["active_scenes"] = {}
if "scenes" not in st.session_state:
    st.session_state["scenes"] = {}
if "actor_scaling" not in st.session_state:
    st.session_state["actor_scaling"] = 1.0
if "session_state_new_actor" not in st.session_state:
    st.session_state["new_actor"] = False


#### Start UI ####

st.title("Hello and welcome to the Schedule Generator")
st.caption("*also known as the susi de-insanator")


with st.expander("CSV Import:"):
    logging.debug("rendering CSV screen")
    ui_csv_import()

with st.expander("Actors:"):
    logging.debug("rendering Actors screen")
    ui_actors()

with st.expander("Scenes:"):
    logging.debug("rendering Scenes screen")
    ui_scenes()

with st.expander("Schedule"):
    logging.debug("rendering Schedule screen")
    ui_schedule()
