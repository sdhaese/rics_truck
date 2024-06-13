# working in SiS but will need to modify for native Streamlit
# Import python packages
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
import snowflake.snowpark as sp
from snowflake.snowpark import Session, Row
import snowflake.connector

##CREATE NEW FUNCTION TO TRY GET ACTIVE SESSION FROM SNOWPARK
##OTHERWISE BUILD CONNECTION
def open_session():
    snow_session = None
 
    try:
      snow_session = get_active_session()
    except:
      #READ CREDS INTO DICTIONARY
        creds = {**st.secrets["snowflake"]}       
        #BUILD SESSION
        snow_session = sp.Session.builder.configs(creds).create()
 
    return snow_session

# # build the api connection
# my_cnx = snowflake.connector.connect(**st.secrets["snowflake"])

# # Get the current credentials
# session = get_active_session()

# Run open session function to create a session
session = open_session()

# Function to fetch minimum precipitation data for a given day
def fetch_min_precip_prob_for_day(day):
    min_precip_prob_table = session.sql(f"call fetch_min_precip_prob_for_any_day({day})").collect()
    df_min_precip_prob = pd.DataFrame(min_precip_prob_table)
    return df_min_precip_prob

# Function to fetch POI sites from frostbyte based on zip code and key words
def fetch_recommended_sites(zip_code, keyword):
    places_to_go = session.sql(f"select location_name from SAFEGRAPH_FROSTBYTE.PUBLIC.FROSTBYTE_TB_SAFEGRAPH_S where postal_code like '{zip_code}' and ({keyword})").collect()
    return places_to_go

# df_tomorrow_rain = st.dataframe(fetch_min_precip_prob_for_day(1))
# li_tomorrow_rain = df_tomorrow_rain.values.tolist()
# st.write(li_tomorrow_rain)
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
          st.dataframe(fetch_recommended_sites(li_tomorrow_rain[i][0], keyword))
    elif li_tomorrow_rain[i][4] > 25 and li_tomorrow_rain[i][4] < 75:
        keyword = "location_name like '%Museum%' or location_name like '%University%' or location_name like '%College%'"
        locations = fetch_recommended_sites(li_tomorrow_rain[i][0], keyword)
        if locations:
          st.write('Seems like it will probably rain in ', li_tomorrow_rain[i][0], ' tomorrow. Here are some places you might still expect lots of foot traffic.' )
          st.dataframe(locations)
    elif li_tomorrow_rain[i][4] >= 75:
        st.write("It's raining everywhere. You should probably stay home.")

