import streamlit as st


st.set_page_config(page_title="Pindu", page_icon="📊", layout="wide")

navigation = st.navigation(
    [
        st.Page("pages/polish_debt.py", title="Dług Polski", icon="📈", default=True),
        st.Page("pages/aktualny_dlug.py", title="Aktualny Dług Polski", icon="💰"),
        st.Page("pages/800_plus.py", title="Program 800+", icon="👨‍👩‍👧‍👦"),
    ]
)

navigation.run()
