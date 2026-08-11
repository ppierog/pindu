import streamlit as st


st.set_page_config(page_title="Pindu", page_icon="📊", layout="wide")

navigation = st.navigation(
    [
        st.Page("pages/1_Dlug_polski.py", title="Dług polski", icon="📈", default=True),
        st.Page("pages/2_800_plus.py", title="Program 800+", icon="👨‍👩‍👧‍👦"),
    ]
)

navigation.run()
