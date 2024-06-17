# working in SiS but will need to modify for native Streamlit
# Import python packages
import streamlit as st
import pandas as pd
from functions.functions import fetch_recipe_details_for_humans, recipe_selected, hide_recipe_details, click_button, fetch_recipe_names, fetch_ingredients, fetch_measurement_units, fetch_recipe_details, add_ingredient, add_measurement_unit, add_recipe, add_ingreds_to_recipe, fetch_recipe_id_from_name, fetch_ingredient_id_from_name, fetch_unit_id_from_name, ingredient_dataframe_for_humans, manually_modify_recipe, insert_into_recipe, open_session

# Run open session function to create a session
session = open_session()

# Function to make st.button stateful
if 'clicked' not in st.session_state:
    st.session_state.clicked = False
    
df_ingredients_list = fetch_ingredients()[1]
df_ingredients_plus_id = fetch_ingredients()[0]

#=====================================================================
# Recipe Viewer
st.title('Recipe Viewer')

#========================================
# Initialize session state for visibility
if 'visible' not in st.session_state:
    st.session_state.visible = False
    st.session_state.current_recipe = ''

# Fetch and display recipe names
recipe_names = fetch_recipe_names()
selected_recipe = st.selectbox('Select a recipe to view', recipe_names, on_change = recipe_selected)

if st.session_state.visible:
    # st.session_state.visible = True
    details = fetch_recipe_details_for_humans(selected_recipe)
    st.write(f'Details for {selected_recipe}:')  

    # Modify selected recipe
    #==============================================================
    # for selecting between new ingredients or measurement units
    if st.button('Modify Selected Recipe'):
        st.session_state.modify_selected_recipe = True
    
    if 'modify_selected_recipe' in st.session_state and st.session_state.modify_selected_recipe:
        if st.button('Cancel Modifications'):
            st.session_state.modify_selected_recipe = False
        else:
            df_selected_recipe_ingredients = ingredient_dataframe_for_humans(selected_recipe)        
            original_length = len(df_selected_recipe_ingredients)
            editable_recipe = st.data_editor(
                df_selected_recipe_ingredients,
                num_rows = "dynamic",
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
                hide_index=True
            )

            if st.button('Commit Recipe Change'):
                for i in range(len(editable_recipe)):
                    if i > (original_length-1):
                        component_order_adder = i+1-original_length
                        insert_into_recipe((editable_recipe['INGREDIENT_NAME'][i]), (editable_recipe['QUANTITY'][i]), editable_recipe['UNIT_NAME'][i], selected_recipe, component_order_adder)
                    else:
                        manually_modify_recipe((editable_recipe['INGREDIENT_NAME'][i]), (editable_recipe['QUANTITY'][i]), editable_recipe['UNIT_NAME'][i], selected_recipe)

                st.success('Recipe Updated')
                st.session_state.modify_selected_recipe = False
    else:
        st.dataframe(details, hide_index=True)
        col1, col2, col3 = st.columns((3, 1, 3))
        with col1:
            make_recipe_button = st.button('Make Recipe')
        with col2:
            make_recipe_for_inv_button = st.button('Make Recipe for Inventory')
        with col3:
            hide_details_button = st.button('Hide Details', on_click = hide_recipe_details)
        


# =========================================================================
# Add Recipe
st.title('Add a recipe')
if st.button('Add Recipe'):
    st.session_state.add_recipe = True

if 'add_recipe' in st.session_state and st.session_state.add_recipe:
    st.write("### Add Recipe")
    if st.button('Copy Existing Recipe'):
        st.session_state.copy_existing = True
        st.session_state.create_from_scratch = False
    if st.button('Create Recipe from Scratch'):
        st.session_state.create_from_scratch = True
        st.session_state.copy_existing = False

# =========================================================================
# Copy Existing Recipe 
if 'copy_existing' in st.session_state and st.session_state.copy_existing:
        with st.form("copy_recipe_form"):
            existing_recipes = fetch_recipe_names()
            recipe_options = [recipe for recipe in existing_recipes]
            selected_recipe = st.selectbox('Select a recipe to copy', recipe_options)
            if selected_recipe:
                recipe_details = fetch_recipe_details(selected_recipe)
                #st.write(recipe_details)
                global new_recipe_name
                new_recipe_name = st.text_input('New Recipe Name', value=selected_recipe + ' Copy')
                global new_recipe_description
                new_recipe_description = st.text_area('New Recipe Description', value='')
                components = []
                ingredient_name_new_recipe_list = []
                for detail in recipe_details:
                    detail_dict = detail.as_dict()
                    ingredient_id_int = int(detail_dict['INGREDIENT_ID'])
                    ingredient_name_new_recipe = session.sql(f"select ingredient_name from ingredients where ingredient_id = {detail_dict['INGREDIENT_ID']}").collect()
                    ingredient_name_new_recipe = [row[0] for row in ingredient_name_new_recipe][0]
                    ingredient_name_new_recipe_list.append(ingredient_name_new_recipe)
                    unit_name_new_recipe = session.sql(f"select unit_name from measurement_units where unit_id = ({detail_dict['UNIT_ID']})").collect()
                    unit_name_new_recipe = [row[0] for row in unit_name_new_recipe][0]
                    ingredient_id = detail[2]
                    unit_id = detail[3]
                    quantity = detail[4]
                    component_order = detail[5]
                    component = {
                        'ingredient_id': ingredient_id,
                        'unit_id': unit_id,
                        'quantity': st.number_input(f'{unit_name_new_recipe} of {ingredient_name_new_recipe}', value=float(quantity), min_value=0.0, step=0.01),
                        'component_order': component_order
                    }
                    components.append(component)
                    
                # find which ingredients are not already included in the recipe before creating a space for additional ingreds
                df_ingredient_name_new_recipe_list = pd.DataFrame(ingredient_name_new_recipe_list)
                df_ingredient_name_new_recipe_list.columns=df_ingredients_list.columns
                missing_ingreds = df_ingredients_list.merge(df_ingredient_name_new_recipe_list.drop_duplicates(), on='INGREDIENT_NAME', how = 'left', indicator=True)
                missing_ingreds = missing_ingreds[missing_ingreds['_merge'] == 'left_only']['INGREDIENT_NAME']
                global addl_ingreds
                addl_ingreds = st.multiselect("Select any additional ingredients to add", missing_ingreds)
                    
            submitted = st.form_submit_button("Save Recipe (don't worry, you can still adjust qtys of additional ingredients")
        if submitted:
            add_recipe(new_recipe_name, new_recipe_description, components)

        # check if additional ingredients need to be added or not
        if len(addl_ingreds) != 0:
            with st.form("additional_ingredients"):
                st.write('Modify Additional Ingredients for ', new_recipe_name)
                components = []
                for item in addl_ingreds:
                    # get recipe_id & ingred_id to write to recipe_components
                    recipe_id = fetch_recipe_id_from_name(new_recipe_name)
                    ingredient_id = fetch_ingredient_id_from_name(item)
                    # let people know what ingred they're working on
                    st.write(item)
                    unit_name = st.selectbox('Select measurement unit', df_unit_names, key = (item + 'unit'))
                    unit_id = fetch_unit_id_from_name(unit_name)
                    quantity = st.number_input('Qty', key = (item + 'qty'))
                    # determine where to put these ingredients in the order
                    max_component_order = [row[0] for row in session.sql(f"select max(component_order) from recipe_components where recipe_id = {recipe_id}").collect()][0]
                    component_order = max_component_order + addl_ingreds.index(item) + 1
                    component = {
                        'ingredient_id': ingredient_id,
                        'unit_id': unit_id,
                        'quantity': quantity,
                        'component_order': component_order
                    }
                    components.append(component)
                submitted2 = st.form_submit_button("Add Ingredients")
            if submitted2:
                add_ingreds_to_recipe(new_recipe_name, components)
        
#===================================================
# Create Recipe from Scratch Section
if 'create_from_scratch' in st.session_state and st.session_state.create_from_scratch:
    st.write("### Create Recipe from Scratch")
    new_recipe_name = st.text_input('Recipe Name')
    new_recipe_description = st.text_area('Recipe Description')
    ingredients = fetch_ingredients()[0]
    units = fetch_measurement_units()[0]
    components = []
    if 'component_count' not in st.session_state:
        st.session_state.component_count = 0
    for i in range(st.session_state.component_count):
        ingredient_options = {ingredient[1]: ingredient[0] for ingredient in ingredients}
        #selected_ingredient = st.selectbox(f'Ingredient {i+1}', list(ingredient_options.keys()))
        selected_ingredient = st.selectbox(f'Ingredient {i+1}', df_ingredients_list)
        unit_options = {unit[1]: unit[0] for unit in units}
        #selected_unit = st.selectbox(f'Unit {i+1}', list(unit_options.keys()))
        selected_unit = st.selectbox(f'Unit {i+1}', df_unit_names)
        quantity = st.number_input(f'Quantity {i+1}', min_value=0.0, step=0.01)
        component = {
            'ingredient_id': fetch_ingredient_id_from_name(selected_ingredient),
            'unit_id': fetch_unit_id_from_name(selected_unit),
            'quantity': quantity,
            'component_order': i+1
        }
        components.append(component)
    if st.button('Add Ingredient'):
        st.session_state.component_count += 1
    if st.button('Save Recipe'):
        add_recipe(new_recipe_name, new_recipe_description, components)
        #st.success('Recipe added successfully!')

#==============================================================
# for selecting between new ingredients or measurement units
if st.button('Add New Ingredient'):
    st.session_state.add_new_ingredient = True
    st.session_state.add_new_measurement_unit = False
if st.button('Add New Measurement Unit'):
    st.session_state.add_new_ingredient = False
    st.session_state.add_new_measurement_unit = True

# ===============================================
# Add New Ingredient
#st.button('Add New Ingredient', on_click = click_button)
#if st.session_state.clicked:
if 'add_new_ingredient' in st.session_state and st.session_state.add_new_ingredient:
    with st.form("ingredient_form"):
        st.write("### Enter ingredient name")
        ingredient_name_input = st.text_input("Ingredient Name")
        submitted = st.form_submit_button("Save Ingredient")
        if submitted:
            add_ingredient(ingredient_name_input)
            st.success('Ingredient Added', icon = "✅")
            st.session_state.add_new_ingredient = False

# ===============================================
# Add New Measurement Unit
# st.button('Add New Measurement Unit', on_click = click_button)
# if st.session_state.clicked:
if 'add_new_measurement_unit' in st.session_state and st.session_state.add_new_measurement_unit:
    with st.form("measurement_unit_form"):
        st.write("### Enter measurement unit")
        unit_name_input = st.text_input("Unit Name")
        submitted = st.form_submit_button("Save Measurement Unit")
        if submitted:
            add_measurement_unit(unit_name_input)
            st.success('Measurement Unit Added', icon = "✅")
            st.session_state.add_new_measurement_unit = False


            
        



