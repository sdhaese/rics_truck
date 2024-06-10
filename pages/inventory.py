# Import python packages
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session, Row


# Get the current credentials
session = get_active_session()

# Function to fetch current inventory
def get_inventory():
    df_inventory = pd.DataFrame(session.sql('select * from inventory_for_humans').collect())
    return df_inventory
df_inventory = get_inventory()

# Function to fetch measurement units
def fetch_measurement_units():
    unitsFull = session.sql('SELECT unit_id, unit_name FROM measurement_units').collect()
    unitsFull = pd.DataFrame(unitsFull)
    unitNames = session.sql('Select unit_name from measurement_units').collect()
    unitNames = pd.DataFrame(unitNames)
    return unitsFull, unitNames
df_unit_names = fetch_measurement_units()[1]

# Function to fetch ingredient_id from ingredient_name
def fetch_ingredient_id_from_name(ingredient_name):
    ingredient_id = session.sql(f"select ingredient_id from ingredients where ingredient_name like '{ingredient_name}'").collect()
    ingredient_id = [row[0] for row in ingredient_id][0]
    return ingredient_id

# Function to fetch unit_id from unit_name
def fetch_unit_id_from_name(unit_name):
    unit_id = session.sql(f"select unit_id from measurement_units where unit_name like '{unit_name}'").collect()
    unit_id = [row[0] for row in unit_id][0]
    return unit_id

# Function to update inventory from manual entries in inventory dataframe
def update_inventory_manual(ingredient_name, qty_available, unit_name):
    ingredient_id = fetch_ingredient_id_from_name(ingredient_name)
    unit_id = fetch_unit_id_from_name(unit_name)
    session.sql(f"""update inventory set qty_available = {qty_available}, unit_id = {unit_id} where ingredient_id = {ingredient_id}""").collect()



st.title('Inventory Management')

#==============================================================
# For manually updating inventory
if st.button('Mannually Edit Inventory'):
    st.session_state.manually_update_inventory = True

if 'manually_update_inventory' in st.session_state and st.session_state.manually_update_inventory:
    editable_inv = st.data_editor(
        df_inventory, 
        column_config={
            'UNIT_NAME': st.column_config.SelectboxColumn(
                "UNIT_NAME",
                options = list(df_unit_names['UNIT_NAME']),
                required = True,
            )
        },
        hide_index=True
    )
    
    if st.button('Commit Inventory Update'):
        for i in range(len(editable_inv)):
            update_inventory_manual((editable_inv['INGREDIENT_NAME'][i]), editable_inv['QTY_AVAILABLE'][i], editable_inv['UNIT_NAME'][i])
            st.session_state.manually_update_inventory = False
        st.success('Inventory Updated')

else:
    st.dataframe(df_inventory)
    
    

# allow manual edit of inventory dataframe
# include a button to reset all values to previous
        


