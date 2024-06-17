# Import python packages
import streamlit as st
import pandas as pd
from functions.functions import open_session, get_inventory, fetch_measurement_units, fetch_ingredient_id_from_name, fetch_unit_id_from_name, update_inventory_manual


# Get the current credentials
session = open_session()

df_inventory = get_inventory()
df_unit_names = fetch_measurement_units()[1]

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
        


