from turtle import down
import streamlit as st
from optimizer import SA_optimiser
from data_input_forms import *
import numpy as np


def check_and_init_session_state(state):
    if state not in st.session_state:
        st.session_state[state] = []


for state in ["actors", "requirements", "dates", "indexes"]:
    check_and_init_session_state(state)

if "np_availabilities" not in st.session_state:
    st.session_state["np_availabilities"] = np.array([])
if "active_scenes" not in st.session_state:
    st.session_state["active_scenes"] = {}
if "scenes" not in st.session_state:
    st.session_state["scenes"] = {}
if "actor_scaling" not in st.session_state:
    st.session_state["actor_scaling"] = 1.0

st.title("Hello and welcome to the Schedule Generator")
st.caption("*also known as the susi de-insanator")


def load_csv_schedule(df):
    import pandas as pd

    df = pd.concat(
        (
            df.iloc[:, 0],
            df.loc[:, st.session_state.date_range[0] : st.session_state.date_range[1]],
        ),
        axis=1,
    )
    st.session_state.dates = df.columns[1:].tolist()
    if df.iloc[0, 0] not in st.session_state.actors:
        st.session_state.actors.extend(df.iloc[:, 0].tolist())
    df_view = df.copy()
    df.replace("Yes", 1, inplace=True)
    df.replace("If need be", 0.3, inplace=True)
    df.replace("No", -1, inplace=True)
    df.replace("No", -1, inplace=True)
    if st.session_state.np_availabilities.size == 0:
        st.session_state.np_availabilities = np.array(df.iloc[:, 1:])
    return df_view


with st.expander("CSV Import:"):
    import pandas as pd

    st.subheader("select file to import availabilities and actors")
    csv_file = st.file_uploader("", type="csv")
    if csv_file:
        df = pd.read_csv(csv_file)
        date_temp = df.columns[1:].values
        st.session_state.date_range = st.select_slider(
            "Select Date Range", date_temp, value=(date_temp[0], date_temp[-1])
        )
        st.dataframe(load_csv_schedule(df))


with st.expander("Actors:"):
    st.subheader("Current Actors:")

    # with col2:
    if st.session_state.actors:
        ac1, ac2, ac3 = st.columns(3)
        per_column = int(len(st.session_state.actors[0]) / 3)
        for i, actor in enumerate(st.session_state.actors):
            if i % 3 == 0:
                with ac1:
                    st.write(actor)
            elif i % 3 == 1:
                with ac2:
                    st.write(actor)
            else:
                with ac3:
                    st.write(actor)

    col1, col2 = st.columns(2)
    with col1:
        create_actors()

    e1, e2 = st.columns(2)
    with e1:
        reset = st.button("!reset actors!")
        if reset:
            st.session_state.actors = []
            st.session_state.np_availabilities = np.array([])
            st.experimental_rerun()
    with e2:
        import json

        st.download_button(
            "Download actors as json",
            data=json.dumps(st.session_state.actors),
            file_name="actors.json",
            mime="json",
        )

    import pandas as pd

    with col2:
        if st.session_state.np_availabilities.size > 0:
            st.subheader("resulting table")
            st.dataframe(
                pd.DataFrame(
                    st.session_state.np_availabilities,
                    columns=st.session_state.dates,
                    index=st.session_state.actors,
                )
            )

with st.expander("Scenes:"):
    st.header("Current Scenes:")
    for scene, actors in st.session_state.scenes.items():
        st.markdown(f"***{scene}*** with **{actors[0]}**, need to be: {actors[1]}")

    col1, col2 = st.columns(2)
    with col1:
        create_scene()
    with col2:
        reset = st.button("!delete all scenes!")
        if reset:
            st.session_state.scenes = {}
            st.experimental_rerun()

        import json

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


def split_scenes_over_columns(use_all):
    num_scenes = len(st.session_state.scenes)
    col1, col2, col3 = st.columns(3)
    for i, scene in enumerate(list(st.session_state.scenes.keys())):
        if i % 3 == 0:
            with col1:
                st.session_state.active_scenes[scene] = st.checkbox(
                    str(scene), disabled=use_all
                )
        elif i % 3 == 1:
            with col2:
                st.session_state.active_scenes[scene] = st.checkbox(
                    str(scene), disabled=use_all
                )
        else:
            with col3:
                st.session_state.active_scenes[scene] = st.checkbox(
                    str(scene), disabled=use_all
                )


def train_and_print(iterations, sa):
    with st.spinner("working on it..."):
        config = sa.train(iterations)
    download_data = create_output(config, sa)

    for col in range(len(download_data.columns)):
        write_md = download_data.loc[
            "Alternate scene", download_data.columns.tolist()[col]
        ]
        if download_data.iloc[0, col] == "No compatible scene found":
            st.markdown(
                f"For the date *{download_data.columns[col]}*, "
                f"there is *no* scene\n\n"
            )
        else:
            st.markdown(
                f"For the date *{download_data.columns[col]}*, "
                f"the scene is **{download_data.iloc[0,col]}** "
                f"with actors {download_data.iloc[1,col]}\n\n"
            )
        if any(write_md):
            st.markdown(f"alternative scenes are {[w for w in write_md.values if w]}")
        st.markdown("---")

    st.download_button(
        "download as csv",
        download_data.to_csv().encode("utf-8"),
        file_name="schedule.csv",
        mime="csv",
    )


def find_alternatives(sa: SA_optimiser):
    alt = []
    for date in range(len(st.session_state.np_availabilities)):
        rank = []
        for i, scene in enumerate(
            [
                st.session_state.requirements[:, i]
                for i in range(len(st.session_state.scenes))
            ]
        ):
            rank.append(
                (
                    i,
                    sa.calculate_overlap(
                        scene, st.session_state.np_availabilities[:, date]
                    ),
                )
            )
        rank = [x for x in rank if x[1] > 0]
        rank.sort(key=lambda x: x[1], reverse=True)
        alt.append(rank[: min(len(rank), 5)])
    return alt


def create_output(config, sa: SA_optimiser):
    columns = []
    scenes = []
    actors = []
    can_make_it = []
    need = []
    md = []
    print(config)
    for i, c in enumerate(config):
        if c != -1:
            # md.append(
            #     f'For date *{st.session_state.dates[i]}*,'
            #     f'the scene is **{list(st.session_state.scenes.keys())[c]}** '
            #     f'with {st.session_state.scenes[list(st.session_state.scenes.keys())[c]][0]}'
            #     '\n\n---\n'
            # )
            columns.append(st.session_state.dates[i])
            scenes.append(list(st.session_state.scenes.keys())[c])
            actors.append(
                st.session_state.scenes[list(st.session_state.scenes.keys())[c]][0]
            )
            need.append(
                st.session_state.scenes[list(st.session_state.scenes.keys())[c]][0]
            )
            temp_df = pd.DataFrame(
                st.session_state.np_availabilities[:, c], index=st.session_state.actors
            )
            temp_df = temp_df.loc[actors[-1]]
            can_make_it.append(list(temp_df[temp_df[0] > 0].index))
        else:
            columns.append(st.session_state.dates[i])
            scenes.append("No compatible scene found")
            actors.append("None")
            need.append(None)
            can_make_it.append(None)
            # md.append(
            # f'there is no scene for date {st.session_state.dates[i]}'
            # '---')
    download_data = pd.DataFrame(
        [scenes, actors, can_make_it, need],
        columns=columns,
        index=["Scene name", "Actors in scene", "Can make it", "Important"],
    )
    alternatives_scenes = find_alternatives(sa)
    scenes_per_date = []
    for a_i, a in enumerate(alternatives_scenes):
        temp_scenes = []
        for s, _ in a:
            if s != config[a_i]:
                temp_scenes.append(list(st.session_state.scenes)[s])
        scenes_per_date.append(temp_scenes)
    temp = []
    for scene in scenes_per_date:
        temp_i = []
        for i in range(max([len(x) for x in scenes_per_date])):
            if len(scene) >= i + 1:
                temp_i.append(scene[i])
            else:
                temp_i.append(False)
        temp.append(temp_i)
    for i in range(len(temp[0])):
        temp_to_row = []
        temp_actors = []
        for t in temp:
            temp_to_row.append(t[i])
            if t[i]:
                temp_actors.append(st.session_state.scenes[t[i]][0])
            else:
                temp_actors.append(None)
        print()
        download_data = pd.concat(
            [
                download_data,
                pd.DataFrame(
                    [temp_to_row, temp_actors],
                    index=[f"Alternate scene", f"Actors needed for scene {i}"],
                    columns=download_data.columns,
                ),
            ],
            axis=0,
        )
    print(download_data)
    return download_data


with st.expander("Schedule"):
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

        import pandas as pd

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
