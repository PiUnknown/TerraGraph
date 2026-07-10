import uuid
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Darukaa.Earth Biodiversity Assistant", page_icon="🌱")
st.title("🌱 Darukaa.Earth — Biodiversity Intelligence Chatbot")
st.caption("Ask about your land's biodiversity, soil, or climate conditions.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_recommendations(recommendations: list[dict]) -> None:
    for i, rec in enumerate(recommendations, start=1):
        with st.container(border=True):
            st.markdown(f"**{i}. {rec['action']}**")
            st.markdown(f"*Why it works:* {rec['mechanism']}")
            st.markdown(f"**Impacted metrics:** {', '.join(rec['impacted_metrics'])}")
            if rec.get("estimated_effect"):
                st.markdown(f"**Estimated effect:** {rec['estimated_effect']}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Time horizon:** {rec['time_horizon'].replace('_', ' ')}")
            with col2:
                st.markdown(f"**Confidence:** {rec.get('confidence', 'n/a')}")
            st.caption(f"Source: {rec['source']}")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("recommendations"):
            render_recommendations(msg["recommendations"])
        else:
            st.write(msg["content"])

user_message = st.chat_input("Describe your land, soil, or ask a question...")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"session_id": st.session_state.session_id, "message": user_message},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                st.error(f"Couldn't reach the backend: {e}")
                st.stop()

        recommendations = data.get("recommendations", [])
        if recommendations:
            st.write(data["message"])
            render_recommendations(recommendations)
            st.session_state.messages.append({
                "role": "assistant",
                "content": data["message"],
                "recommendations": recommendations,
            })
        else:
            st.write(data["message"])
            st.session_state.messages.append({"role": "assistant", "content": data["message"]})