import streamlit as st
import pandas as pd
from modules.optimizer import SA_optimiser
import numpy as np
import logging

def write_list_3_col():
    # st.write(st.session_state.actors)
    ac1, ac2, ac3 = st.columns(3)
        # per_column = int(len(st.session_state.actors) / 3)
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
def load_csv_schedule(df):
    import pandas as pd
    logging.debug("loading availabilities")
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
    df = replace_entries_in_df(df)
    
    st.session_state.np_availabilities = np.array(df.iloc[:, 1:], dtype=np.float16)
    logging.debug(f"availabilities are {st.session_state.np_availabilities}")
    return df

def replace_entries_in_df(df):
    logging.debug("Replacing keywords in availabilities with numeric values")
    df = df.applymap(lambda x: x.lower())
    df.replace(["Yes", "yes", "YES"], 1, inplace=True)
    df.replace(
        ["if need be", "IF NEED BE", "If Need Be", "If need be"], 0.3, inplace=True
    )
    df.fillna(-1, inplace=True)
    df.replace(["No", "NO", "no", "<na>", "na", "NA"], -1, inplace=True)
    return df

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
    for date in range(len(st.session_state.np_availabilities[0])):
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
    print(f"creating output based on {config}")

    columns, scenes, actors, can_make_it, need = get_config_results(config)

    download_data = pd.DataFrame(
        [scenes, actors, can_make_it, need],
        columns=columns,
        index=["Scene name", "Actors in scene", "Can make it", "Important"],
    )
    alternatives_scenes = find_alternatives(sa)
    temp = filter_and_pad_scenes(config, alternatives_scenes)
    
    download_data = append_alt_scenes_to_output(temp, download_data)
    print(download_data)
    return download_data

def append_alt_scenes_to_output(temp, download_data):
    for date_index in range(len(temp[0])):
        temp_to_row = []
        temp_actors = []
        for t in temp:
            temp_to_row.append(t[date_index])
            if t[date_index]:
                temp_actors.append(sorted(st.session_state.scenes[t[date_index]]["0"]))
            else:
                temp_actors.append(None)

        download_data = pd.concat(
            [
                download_data,
                pd.DataFrame(
                    [temp_to_row, temp_actors],
                    index=[f"Alternate scene", f"Actors needed for scene {date_index}"],
                    columns=download_data.columns,
                ),
            ],
            axis=0,
        )
    return download_data

def filter_and_pad_scenes(config, alternatives_scenes):
    scenes_per_date = []
    for a_i, a in enumerate(alternatives_scenes):
        temp_scenes = []
        for s, _ in a:
            if s != config[a_i]:
                temp_scenes.append(list(st.session_state.scenes)[s])
        scenes_per_date.append(temp_scenes)
    temp = []
    pad_scene_list_to_max_scene_number(scenes_per_date, temp)
    return temp

def pad_scene_list_to_max_scene_number(scenes_per_date, temp):
    for scene in scenes_per_date:
        temp_i = []
        for date_index in range(max([len(x) for x in scenes_per_date])):
            if len(scene) >= date_index + 1:
                temp_i.append(scene[date_index])
            else:
                temp_i.append(False)
        temp.append(temp_i)

def get_config_results(config): 
    columns = []
    scenes = []
    actors =[]
    can_make_it = []
    need = []
    for date_index, scene_number in enumerate(config):
        columns.append(st.session_state.dates[date_index])
        if scene_number != -1:
            scenes.append(list(st.session_state.scenes.keys())[scene_number])
            actors.append(
                sorted(
                    st.session_state.scenes[
                        list(st.session_state.scenes.keys())[scene_number]
                    ]["0"]
                )
            )
            need.append(
                sorted(
                    st.session_state.scenes[
                        list(st.session_state.scenes.keys())[scene_number]
                    ]["1"]
                )
            )
            available_on_day = []
            for available, name in zip(st.session_state.np_availabilities[:, date_index],st.session_state.actors):
                if available == 1:
                    available_on_day.append(name)                    
            # temp_df = pd.DataFrame(
            #     st.session_state.np_availabilities[:, date_index],
            #     index=st.session_state.actors,
            # )
            # available_on_day = [actor for actor in actors[-1] if actor in temp_df.index] 
            can_make_it.append(sorted(available_on_day))

            
        else:
            scenes.append("No compatible scene found")
            actors.append("None")
            need.append(None)
            can_make_it.append(None)
    return columns, scenes, actors, can_make_it, need
