"""Direct person selection with a durable, ID-based session choice."""

import streamlit as st


def select_person(persons, *, container=None, key="chart_person", label="Odaberi osobu", default_index=0):
    if not persons:
        return None
    container = container if container is not None else st.sidebar
    by_id = {person.id: person for person in persons}
    ids = list(by_id)
    saved_key = f"{key}_selected_id"
    widget_key = f"{key}_radio"
    if st.session_state.get(saved_key) not in by_id:
        st.session_state[saved_key] = ids[min(default_index, len(ids) - 1)]
    # A widget can disappear on another page; keep the choice separately.
    if st.session_state.get(widget_key) != st.session_state[saved_key]:
        st.session_state[widget_key] = st.session_state[saved_key]

    def remember_selection():
        st.session_state[saved_key] = st.session_state[widget_key]

    labels = {}
    for person in persons:
        text = f"{person.name} ({person.birth_date})"
        labels[person.id] = text
    original_labels = list(labels.values())
    for person_id, text in list(labels.items()):
        if original_labels.count(text) > 1:
            # Also distinguish records with identical names and birth dates.
            labels[person_id] = f"{text} · #{person_id}"

    selected_id = container.radio(
        label, ids, key=widget_key, format_func=labels.__getitem__,
        on_change=remember_selection,
    )
    return by_id[selected_id]
