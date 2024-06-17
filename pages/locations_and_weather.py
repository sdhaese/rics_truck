# working in SiS but will need to modify for native Streamlit
# Import python packages
import streamlit as st
import pandas as pd
from functions.functions import open_session, fetch_min_precip_prob_for_day, fetch_recommended_sites

# Run open session function to create a session
session = open_session()

df_tomorrow_rain = fetch_min_precip_prob_for_day(1)
st.dataframe(df_tomorrow_rain)
li_tomorrow_rain = df_tomorrow_rain.values.tolist()

for i in range(len(li_tomorrow_rain)):
    # st.write(li_tomorrow_rain[i][0])
    if li_tomorrow_rain[i][4] <= 25:
        keyword = "location_name like '%Park%'"
        locations = fetch_recommended_sites(li_tomorrow_rain[i][0], keyword)
        if locations:
            st.write('There is little to no chance of rain in ', li_tomorrow_rain[i][0], ' tomorrow. Here are some parks you can expect lots of people to be.')
            st.dataframe(locations)
    elif li_tomorrow_rain[i][4] > 25 and li_tomorrow_rain[i][4] < 75:
        keyword = "location_name like '%Museum%' or location_name like '%University%' or location_name like '%College%'"
        locations = fetch_recommended_sites(li_tomorrow_rain[i][0], keyword)
        if locations:
          st.write('Seems like it will probably rain in ', li_tomorrow_rain[i][0], ' tomorrow. Here are some places you might still expect lots of foot traffic.' )
          st.dataframe(locations)
    elif li_tomorrow_rain[i][4] >= 75:
        st.write("It's raining everywhere. You should probably stay home.")

