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

session = open_session()

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

def click_button():
    st.session_state.clicked = True

# Function to fetch recipe names
def fetch_recipe_names():
    recipe_names = session.sql('SELECT recipe_name FROM recipes').collect()
    for i in range(len(recipe_names)):
        recipe_names[i] = [row[0] for row in recipe_names][i]
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
    

# Function to fetch current inventory
def get_inventory():
    df_inventory = pd.DataFrame(session.sql('select * from inventory_for_humans').collect())
    return df_inventory

# Function to update inventory from manual entries in inventory dataframe
def update_inventory_manual(ingredient_name, qty_available, unit_name):
    ingredient_id = fetch_ingredient_id_from_name(ingredient_name)
    unit_id = fetch_unit_id_from_name(unit_name)
    session.sql(f"""update inventory set qty_available = {qty_available}, unit_id = {unit_id} where ingredient_id = {ingredient_id}""").collect()

# Function to fetch minimum precipitation data for a given day
def fetch_min_precip_prob_for_day(day):
    min_precip_prob_table = session.sql(f"call fetch_min_precip_prob_for_any_day({day})").collect()
    df_min_precip_prob = pd.DataFrame(min_precip_prob_table)
    return df_min_precip_prob

# Function to fetch POI sites from frostbyte based on zip code and key words
def fetch_recommended_sites(zip_code, keyword):
    places_to_go = session.sql(f"select location_name from SAFEGRAPH_FROSTBYTE.PUBLIC.FROSTBYTE_TB_SAFEGRAPH_S where postal_code like '{zip_code}' and ({keyword})").collect()
    return places_to_go

# Function to insert a new line into inventory
def insert_inventory_line(ingredient_name, qty, unit_name):
    ingredient_id = fetch_ingredient_id_from_name(ingredient_name)
    unit_id = fetch_unit_id_from_name(unit_name)
    session.sql(f"insert into inventory (ingredient_id, qty_available, unit_id) values ({ingredient_id}, {qty}, {unit_id})").collect()

# Function to subtract igredients from inventory
# def subtract_from_inventory():