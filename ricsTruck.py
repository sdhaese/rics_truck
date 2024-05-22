import streamlit as st

conn = st.connection("snoflake")

df = conn.query("SELECT * from recipes;", ttl=600)
