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