# working in SiS but will need to modify for native Streamlit
# Import python packages
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session, Row
import snowflake.connector

# build the api connection
my_cnx = snowflake.connector.connect(**streamlit.secrets["snowflake"])

# Get the current credentials
session = get_active_session()

# Function to fetch recipe details
def fetch_recipe_details_for_humans(recipe_name):
    recipes_for_humans = session.sql(f"CALL recipes_for_humans_by_name('{recipe_name}')").collect()
    return recipes_for_humans

# Function to use in the recipe viewer dropdown callback
def recipe_selected():
    # global recipe_selected_to_view
    # recipe_selected_to_view = True
    st.session_state.visible = True

# Function used to hide recipe details
def hide_recipe_details():
    # global recipe_selected_to_view
    # recipe_selected_to_view = False
    st.session_state.visible = False

# Function to make st.button stateful
if 'clicked' not in st.session_state:
    st.session_state.clicked = False
    
def click_button():
    st.session_state.clicked = True

# Function to fetch recipe names
def fetch_recipe_names():
    recipe_names = session.sql('SELECT recipe_name FROM recipes').collect()
    return recipe_names

# Function to fetch ingredients
def fetch_ingredients():
    ingredientsFull = session.sql('SELECT ingredient_id, ingredient_name FROM ingredients').collect()
    ingredientsFull = pd.DataFrame(ingredientsFull)
    just_ingredients = session.sql('SELECT ingredient_name FROM ingredients').collect()
    just_ingredients = pd.DataFrame(just_ingredients)
    return ingredientsFull, just_ingredients

df_ingredients_list = fetch_ingredients()[1]
df_ingredients_plus_id = fetch_ingredients()[0]


# Function to fetch measurement units
def fetch_measurement_units():
    unitsFull = session.sql('SELECT unit_id, unit_name FROM measurement_units').collect()
    unitsFull = pd.DataFrame(unitsFull)
    unitNames = session.sql('Select unit_name from measurement_units').collect()
    unitNames = pd.DataFrame(unitNames)
    return unitsFull, unitNames
    
df_unit_names = fetch_measurement_units()[1]


# Function to fetch recipe details
def fetch_recipe_details(recipe_name):
    recipeDetails = session.sql(f"SELECT * FROM recipe_components WHERE recipe_id = (SELECT recipe_id FROM recipes WHERE recipe_name = '{recipe_name}')").collect()
    return recipeDetails

# Function to add a new ingredient
def add_ingredient(ingredient_name):
    session.sql(f"""INSERT INTO rics_food_truck.foodstuff.ingredients (INGREDIENT_NAME) VALUES ('{ingredient_name}')""").collect()

# Function to add a new measurement unit
def add_measurement_unit(unit_name):
    session.sql(f"""INSERT INTO rics_food_truck.foodstuff.measurement_units (UNIT_NAME) VALUES ('{unit_name}')""").collect()

# Function to add a new recipe
def add_recipe(recipe_name, recipe_description, components):
    old_id = session.sql("SELECT MAX(recipe_id) FROM recipes").collect()
    # check if a recipe name already exists in recipes
    check_name = session.sql(f"select * from recipes where recipe_name like '{recipe_name}'").collect()
    if len(check_name) == 0:
        session.sql(f"INSERT INTO recipes (recipe_name, description) VALUES ('{recipe_name}', '{recipe_description}')").collect()
        
        # Retrieve the last inserted recipe_id
        new_id = session.sql("SELECT MAX(recipe_id) FROM recipes").collect()
        new_id = [row[0] for row in new_id][0]
        check_id = session.sql(f"select * from recipe_components where recipe_id like '{new_id}'").collect()
        if len(check_id) == 0:
            for component in components:
                if component['quantity'] != 0:
                    session.sql(f"""
                        INSERT INTO rics_food_truck.foodstuff.recipe_components (RECIPE_ID, ingredient_id, unit_id, quantity, component_order)
                        VALUES ('{new_id}', {component['ingredient_id']}, {component['unit_id']}, {component['quantity']}, {component['component_order']})
                    """).collect()
            session.sql(f""" call sub_recipe('{recipe_name}')""").collect()
            st.success('Recipe Added')
        else:
            st.error('Recipe is already listed in recipe components table')
    else:
        st.error('Recipe name already exists')

# Function to add ingredients to an existing recipe
def add_ingreds_to_recipe(recipe_name, components):
    # first get the recipe_id of the recipe
    recipe_id = session.sql(f"select recipe_id from recipes where recipe_name like '{recipe_name}'").collect()
    recipe_id = [row[0] for row in recipe_id][0]
    # check that recipe_id present in recipe_components
    check_id = session.sql(f"select * from recipe_components where recipe_id like '{recipe_id}'").collect()
    if len(check_id) != 0: # verify the recipy already exists in recipe_components
        for component in components:
            #if component['quantity'] != 0:
            session.sql(f"""
                INSERT INTO rics_food_truck.foodstuff.recipe_components (RECIPE_ID, ingredient_id, unit_id, quantity, component_order)
                VALUES ('{recipe_id}', {component['ingredient_id']}, {component['unit_id']}, {component['quantity']}, {component['component_order']})
            """).collect()
        st.success('Ingredients Added')
    else:
        st.error('Recipe does not exist in recipe components table')

# Function to fetch recipe_id from recipe_name
def fetch_recipe_id_from_name(recipe_name):
    recipe_id = session.sql(f"select recipe_id from recipes where recipe_name like '{recipe_name}'").collect()
    recipe_id = [row[0] for row in recipe_id][0]
    return recipe_id

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

# Function to return a human readable dataframe with all the components of a selected recipe
def ingredient_dataframe_for_humans(recipe_name):
    recipe_id = fetch_recipe_id_from_name(recipe_name)
    df_selected_recipe_ingredients = session.sql(f"call dataframe_recipes_for_humans_by_id({recipe_id})").collect()
    df_selected_recipe_ingredients = pd.DataFrame(df_selected_recipe_ingredients)
    return df_selected_recipe_ingredients

# Function to write recipe mods back to recipe_components
def manually_modify_recipe(ingredient_name, quantity, unit_name, recipe_name):
    recipe_id = fetch_recipe_id_from_name(recipe_name)
    ingredient_id = fetch_ingredient_id_from_name(ingredient_name)
    unit_id = fetch_unit_id_from_name(unit_name)
    session.sql(f"update recipe_components set quantity = {quantity}, unit_id = {unit_id} where ingredient_id = {ingredient_id} and recipe_id = {recipe_id}").collect()

# Function to insert changes into existing recipe
def insert_into_recipe(ingredient_name, quantity, unit_name, recipe_name, component_order_adder):
    recipe_id = fetch_recipe_id_from_name(recipe_name)
    ingredient_id = fetch_ingredient_id_from_name(ingredient_name)
    unit_id = fetch_unit_id_from_name(unit_name)
    max_component_order = session.sql(f"select max(component_order) from recipe_components where recipe_id = {recipe_id}").collect()
    max_component_order = [row[0] for row in max_component_order][0]
    component_order = max_component_order + component_order_adder
    session.sql(f"""insert into recipe_components (recipe_id, ingredient_id, unit_id, quantity, component_order) values ({recipe_id}, {ingredient_id}, {unit_id}, {quantity}, {component_order})""").collect()
    
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
        st.button('Hide Details', on_click = hide_recipe_details)


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


            
        



