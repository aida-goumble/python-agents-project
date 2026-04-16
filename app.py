import streamlit as st

from agent import construire_tools, creer_agent


st.set_page_config(page_title="Agent TP", page_icon="🤖", layout="centered")


def _reset():
    for k in ("messages", "agent"):
        if k in st.session_state:
            del st.session_state[k]


st.title("Agent (LangChain)")

with st.sidebar:
    st.header("Outils disponibles")
    for t in construire_tools():
        name = getattr(t, "name", t.__class__.__name__)
        desc = getattr(t, "description", "")
        st.markdown(f"**{name}**")
        if desc:
            st.caption(desc)
        st.divider()

    if st.button("Réinitialiser la conversation"):
        _reset()
        st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = creer_agent()


for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


question = st.chat_input("Pose ta question")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Réflexion..."):
            res = st.session_state.agent.invoke({"input": question})
            output = res.get("output", "")
        st.markdown(output)

    st.session_state.messages.append({"role": "assistant", "content": output})
