import streamlit as st
import pandas as pd
import json
import numpy as np
from modules.data_input_forms import check_actors_to_scenes, create_actors, create_scene, create_scene_requirements_matrix
from modules.optimizer import SA_optimiser
from modules.ui_utils import load_csv_schedule, write_list_3_col, split_scenes_over_columns, train_and_print

def ui_csv_import():
    st.subheader("select file to import availabilities and actors")
    csv_file = st.file_uploader("", type="csv")
    if csv_file:
        df = pd.read_csv(csv_file)
        
        st.session_state.date_start = st.number_input(
            "column when dates_start",
            min_value=0,
            max_value=df.shape[1],
            step=1,
            value=1,
        )
        st.write(f"colums =  {df.columns}")
        date_temp = df.columns[st.session_state.date_start :].values

        st.session_state.date_range = st.select_slider(
            "Select Date Range", date_temp, value=(date_temp[0], date_temp[-1])
        )
        
        st.write("Check that the Data is correctly loaded:")
        st.dataframe(load_csv_schedule(df))

def ui_actors():
    st.subheader("Current Actors:")

    if st.session_state.actors:
        write_list_3_col()

    st.session_state.new_actor = st.checkbox("new actor creation")
    if st.session_state.new_actor:
        create_actors()

    e1, e2 = st.columns(2)
    with e1:
        reset = st.button("!reset actors!")
        if reset:
            st.session_state.actors = []
            st.session_state.np_availabilities = np.array([])
            st.experimental_rerun()
    with e2:
        st.download_button(
            "Download actors as json",
            data=json.dumps(st.session_state.actors),
            file_name="actors.json",
            mime="json",
        )

    if st.session_state.np_availabilities.size > 0:
        st.subheader("resulting table")
        st.dataframe(
            pd.DataFrame(
                st.session_state.np_availabilities,
                columns=st.session_state.dates,
                index=st.session_state.actors,
            )
        )


def ui_scenes():
    st.header("Current Scenes:")
    for scene, actors in st.session_state.scenes.items():
        st.markdown(f"***{scene}*** with **{actors['0']}**, need to be: {actors['1']}")

    col1, col2 = st.columns(2)
    with col1:
        create_scene()
    with col2:
        reset = st.button("!delete all scenes!")
        if reset:
            st.session_state.scenes = {}
            st.experimental_rerun()

        st.download_button(
            "Download scenes as json",
            data=json.dumps(st.session_state.scenes),
            file_name="scenes.json",
            mime="json",
        )

        scenes_json = st.file_uploader("Upload scenes file", type="json")
        if scenes_json:
            scenes = json.loads(scenes_json.read())
            if list(scenes.keys())[0] not in st.session_state.scenes:
                st.session_state.scenes = st.session_state.scenes | scenes
                st.experimental_rerun()
            if problems := check_actors_to_scenes(
                st.session_state.scenes, st.session_state.actors
            ):
                for problem in problems:
                    st.write(problem)


def ui_schedule():
    if st.session_state.scenes:
        st.subheader("scene importance matrix")
        st.session_state.actor_scaling = st.slider(
            "actor importance scaling (as how many actors does one important one count)",
            1.0,
            6.0,
            1.0,
            0.1,
        )
        st.session_state.requirements = create_scene_requirements_matrix(
            st.session_state.scenes,
            st.session_state.actors,
            st.session_state.actor_scaling,
        )

        st.dataframe(
            pd.DataFrame(
                st.session_state.requirements,
                columns=list(st.session_state.scenes.keys()),
                index=st.session_state.actors,
            )
        )
        st.subheader("select scenes to be used: (leave empty to select all)")
        use_all = st.checkbox("Use all scenes")

        split_scenes_over_columns(use_all)

        st.header("Optimization")
        iterations = st.slider(
            "number of optimization steps", 1000, 50000, step=500, value=15000
        )

        if use_all or all(
            [x == False for k, x in st.session_state.active_scenes.items()]
        ):
            sa = SA_optimiser(
                st.session_state.requirements, st.session_state.np_availabilities
            )
        else:
            selected_scenes = [
                list(st.session_state.scenes.keys()).index(s)
                for s, active in st.session_state.active_scenes.items()
                if active
            ]
            sa = SA_optimiser(
                st.session_state.requirements[:, selected_scenes],
                st.session_state.np_availabilities,
            )
        train = st.button("calculate")
        if train:
            train_and_print(iterations, sa)
    else:
        st.info("Plese define actors, scenes and a schedule.")
