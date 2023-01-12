import streamlit as st


def create_scene():
    def submit_scene(
        name,
        actors,
        important_actors,
    ):
        if name == "":
            return
        if name in [n for n in st.session_state.scenes]:
            st.warning("name already in use")
            return
        st.session_state.scenes[name] = (actors, important_actors)
        st.session_state.selected_actors = []
        st.session_state.important_actors = []

    st.header("New Scene:\nPlease fill in the details")
    name = st.text_input("Scene Name:")
    actors = st.multiselect(
        "Actors in scene", st.session_state.actors, key="selected_actors"
    )  # fill from actor objects
    important_actors = st.multiselect(
        "Important actors in scene", actors, key="important_actors"
    )  # fill from actor objects
    st.button("Submit", on_click=submit_scene, args=(name, actors, important_actors))


def create_actors():
    with st.form("Create new actor"):
        st.header("New Actor:\nPlease fill in the details")
        name = st.text_input("Actor Name:", placeholder="enter text here")
        available_on = {}
        for date in st.session_state.dates:
            available_on[date] = st.select_slider(date, ["No", "If need be", "Yes"])
        for k, v in available_on.items():
            if v.lower() in ("no", "<na>", None):
                available_on[k] = 0
            if v.lower() in ("if need be", "if need"):
                available_on[k] = 0.3
            if v.lower() in ("yes"):
                available_on[k] = 1

        submitted = st.form_submit_button("Submit")
        if submitted:
            if name == "":
                return
            if name in st.session_state.actors:
                st.warning("name already in use")
                return
            print("*******")
            st.session_state.actors.append(name)
            st.warning("TODO")
            st.session_state.np_availabilities = np.append(
                st.session_state.np_availabilities,
                [[v for k, v in available_on.items()]],
                axis=0,
            )
            st.experimental_rerun()


import numpy as np


@st.cache
def create_scene_requirements_matrix(scenes: dict, actors: list, scaling: float):
    scene_requirements = [
        convert_scene_to_one_hot(
            scenes[scene]["0"], actors, scenes[scene]["1"], scaling
        )
        for scene in scenes
    ]
    return np.array(scene_requirements).T


@st.cache
def calculate_overlap(
    requirements: np.ndarray,
    availabilities: np.ndarray,
):
    return sum(requirements * availabilities)


@st.cache
def convert_scene_to_one_hot(
    scene: list, actors: list, need_actors: list, scaling: float = 1.5
):
    one_hot = []
    for actor in actors:
        if actor in scene:
            if actor in need_actors:
                one_hot.append(scaling)
            else:
                one_hot.append(1)
        else:
            one_hot.append(0)
    return one_hot


@st.cache
def check_actors_to_scenes(scenes, actors):
    problems = []
    missing_actors = []
    for _, in_scene in scenes.items():
        for actor in in_scene["0"]:
            if actor not in actors:
                problems.append(f"WARNING! {actor} missing in availabilities")
                missing_actors.append(actor)

    if problems == []:
        return False
    else:
        return (set(problems), missing_actors)
