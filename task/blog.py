import sqlite3
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('--ingredients')
parser.add_argument('--meals')
inputs = parser.parse_args()

db_name = sys.argv[1]
conn = sqlite3.connect(db_name)
cursor_name = conn.cursor()


cursor_name.execute('PRAGMA foreign_keys = ON;')
cursor_name.execute('''CREATE TABLE IF NOT EXISTS meals (
                             meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             meal_name VARCHAR(100) NOT NULL UNIQUE );''')
cursor_name.execute('''CREATE TABLE IF NOT EXISTS ingredients (
                             ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             ingredient_name VARCHAR(100) NOT NULL UNIQUE);''')
cursor_name.execute('''CREATE TABLE IF NOT EXISTS measures (
                             measure_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             measure_name VARCHAR(100) UNIQUE);''')
cursor_name.execute('''INSERT  OR IGNORE INTO meals ("meal_name") VALUES ("breakfast"), ("brunch"), ("lunch"), ("supper");''')
cursor_name.execute(''' INSERT OR IGNORE INTO ingredients ("ingredient_name") VALUES ("milk"), ("cacao"), ("strawberry"), ("blueberry"), 
                             ("blackberry"), ("sugar");''')
cursor_name.execute('''INSERT OR IGNORE INTO measures ("measure_name") VALUES ("ml"), ("g"), ("l"), ("cup"), ("tbsp"), ("tsp"), ("dsp"), ("");''')
conn.commit()
cursor_name.execute('''CREATE TABLE IF NOT EXISTS recipes (
                        recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipe_name VARCHAR(100) NOT NULL,
                        recipe_description VARCHAR(300));''')
conn.commit()
cursor_name.execute('''CREATE TABLE IF NOT EXISTS serve (
                        serve_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipe_id INT NOT NULL,
                        meal_id INT NOT NULL,
                        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
                        FOREIGN KEY (meal_id) REFERENCES meals(meal_id));''')
conn.commit()
cursor_name.execute('''CREATE TABLE IF NOT EXISTS quantity (
                        quantity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quantity INTEGER NOT NULL,
                        recipe_id INTEGER NOT NULL,
                        measure_id INTEGER NOT NULL,
                        ingredient_id INTEGER NOT NULL,
                        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
                        FOREIGN KEY (measure_id) REFERENCES measures(measure_id),
                        FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id));''')
conn.commit()

def find_recipe(ingredients, meals):
    recipe_ids = []
    recipe_ids_meal = []
    for ingredient in ingredients:
        recipe_ids.append(set(cursor_name.execute(
            f'SELECT recipe_id FROM quantity JOIN ingredients ON quantity.ingredient_id = ingredients.ingredient_id WHERE ingredients.ingredient_name = "{ingredient}";').fetchall()))
    recipe_id = set.intersection(*recipe_ids)
    for meal in meals:
        recipe_ids_meal.append(set(cursor_name.execute(
            f'SELECT recipe_id FROM serve JOIN meals ON serve.meal_id = meals.meal_id WHERE meals.meal_name = "{meal}";').fetchall()))
    recipe_id_meal = set.union(*recipe_ids_meal)
    ids = recipe_id.intersection(recipe_id_meal)
    print('id', ids)
    recipes = []
    for id in ids:
        recipes.append(cursor_name.execute(f'SELECT recipe_name FROM recipes WHERE recipe_id = {id[0]};').fetchone()[0])
    return ','.join(recipes)

if inputs.ingredients and inputs.meals:
    ingredients = inputs.ingredients.split(",")
    meals = inputs.meals.split(",")
    recipes = find_recipe(ingredients, meals)
    if recipes:
        print('Recipes selected for you:', recipes)
    else:
        print('There are no such recipes in the database.')
else:
    name = input("Recipe name: ")
    while name != '':
        description = input('Recipe description: ')
        sql = 'INSERT INTO recipes ("recipe_name", "recipe_description") VALUES (?,?);'
        recipe_id = cursor_name.execute(sql, (name, description)).lastrowid
        print('recipe id', recipe_id)
        recipes = cursor_name.execute("SELECT * FROM recipes")
        recipes = recipes.fetchall()
        result = cursor_name.execute('SELECT * FROM meals;')
        all_rows = result.fetchall()
        conn.commit()
        print(all_rows)
        serves = input('When this dish can be served? Enter the number: ').split()
        ingredients = input("Please enter the quantity, measure and ingredient name:")
        while ingredients != '':
            ingredients = ingredients.split()
            if len(ingredients) > 2:
                quan = ingredients[0]
                measure = ingredients[1]
                ingredient = ingredients[2]
                measures_id = cursor_name.execute('SELECT measure_id FROM measures WHERE measure_name LIKE (?);',
                                                  ((measure + '%'),)).fetchall()
            else:
                quan = ingredients[0]
                measure = ''
                ingredient = ingredients[1]
                measures_id = cursor_name.execute('SELECT measure_id FROM measures WHERE measure_name = "";').fetchall()
            ingredients_id = cursor_name.execute('SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE (?);',
                                                 (('%' + ingredient + '%'), )).fetchall()
            if len(measures_id) > 1:
                print('The measure is not conclusive!')
            if len(ingredients_id) > 1:
                print('The ingredient is not conclusive!')
            if len(measures_id) == 1 and len(ingredients_id) == 1:
                sql = 'INSERT INTO quantity ("quantity", "recipe_id", "measure_id", "ingredient_id") VALUES (?, ?, ?, ?);'
                cursor_name.execute(sql, ( quan, recipe_id, measures_id[0][0], ingredients_id[0][0]))
                conn.commit()
            ingredients = input("Please enter the quantity, measure and ingredient name:")

        for serve in serves:
            sql = f'INSERT INTO serve ("meal_id", "recipe_id") VALUES ("{serve}", "{recipe_id}");'
            cursor_name.execute(sql)
            result = cursor_name.execute('SELECT * FROM serve;')
            conn.commit()
        name = input("Recipe name:")

conn.commit()
conn.close()
