# Import python packages
import streamlit as st
import pandas as pd
from functions.functions import open_session, get_inventory, fetch_measurement_units, fetch_ingredient_id_from_name, fetch_unit_id_from_name, update_inventory_manual, fetch_ingredients, insert_inventory_line


# Get the current credentials
session = open_session()

df_inventory = get_inventory()
original_inv_len = len(df_inventory) - 1
df_unit_names = fetch_measurement_units()[1]
df_ingredients_list = fetch_ingredients()[1]
df_not_in_inventory = not_in_inventory = df_ingredients_list[~df_ingredients_list['INGREDIENT_NAME'].isin(df_inventory['INGREDIENT_NAME'])]

st.title('Inventory Management')

#==============================================================
# For manually updating inventory
if st.button('Mannually Edit Inventory'):
    st.session_state.manually_update_inventory = True

if 'manually_update_inventory' in st.session_state and st.session_state.manually_update_inventory:
    editable_inv = st.data_editor(
        df_inventory, 
        column_config={
            'INGREDIENT_NAME': st.column_config.SelectboxColumn(
                "INGREDIENT_NAME",
                options = list(df_ingredients_list['INGREDIENT_NAME']),
                required = True,
            ),
            'UNIT_NAME': st.column_config.SelectboxColumn(
                "UNIT_NAME",
                options = list(df_unit_names['UNIT_NAME']),
                required = True,
            )
        },
        hide_index=True,
        num_rows = "dynamic"
    )
    
    if st.button('Commit Inventory Update'):
        for i in range(len(editable_inv)):
            if i > original_inv_len:
                insert_inventory_line((editable_inv['INGREDIENT_NAME'][i]), editable_inv['QTY_AVAILABLE'][i], editable_inv['UNIT_NAME'][i])
            else:
                update_inventory_manual((editable_inv['INGREDIENT_NAME'][i]), editable_inv['QTY_AVAILABLE'][i], editable_inv['UNIT_NAME'][i])
        st.session_state.manually_update_inventory = False
        st.success('Inventory Updated')

else:
    st.dataframe(df_inventory, hide_index = True)
    
    

# allow manual edit of inventory dataframe
# include a button to reset all values to previous
        


