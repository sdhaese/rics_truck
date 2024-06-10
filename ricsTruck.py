import streamlit as st

conn = st.connection("snowflake")

df = conn.query("SELECT * from recipes;", ttl=600)
