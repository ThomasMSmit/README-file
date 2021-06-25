import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for, g)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
if os.path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", 'mongodb://localhost')
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

# MongoDb collection variables
# mogelijk weg
users = mongo.db.users
cuisines = mongo.db.cuisines
recipes = mongo.db.recipes
allergens = mongo.db.allergens
ingredients = mongo.db.ingredients

# vervangen met lokale img
placeholder_image = 'http://placehold.jp/48/dedede/adadad/400x400.jpg?text=Image%20Not%20Available'


# Manage session user
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

#Home page
@app.route('/')
def home():
    
    return render_template('home.html')

#Sign up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Function for registering a new user.
    Also checks if username and/or password
    already exists in the database.
    Redirects to recipelist
    """
    # Checks if user is not already logged in
    if g.user in session:
        flash('You are already registered!')
        return redirect(url_for('login'))

    # Checks if the passwords match
    if request.method == 'POST':
        form = request.form.to_dict()
        if form['password'] == form['password1']:
            registered_user = users.find_one(
                            {"username": form['username']})
    # Checks if username already exists
            if registered_user:
                flash("Username already taken")
                return redirect(url_for('signup'))
    # Hashes the password and puts new user in db
            else:
                hashed_password = generate_password_hash(form['password'])
                users.insert_one(
                    {
                        'username': form['username'],
                        'password': hashed_password
                    }
                )
                user_in_db = users.find_one(
                        {"username": form['username']})
                if user_in_db:
                    session['user'] = user_in_db['username']
                    flash("Account successfully created")
                    return redirect(url_for('signup'))
                else:
                    flash("There was a problem. Please try again.")
                    return redirect(url_for('signup'))
        else:
            flash("Passwords don't match")
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # Retrieve users from database and check that username exists
        form = request.form.to_dict()
        username_entered = request.form.get('username')
        this_user_in_db = users.find_one({'username': username_entered})
        if not this_user_in_db:
            flash('Username does not exist', 'error')
            return render_template('login.html')

        # once username exists in database confirm password entered
        # and that both fields are populated
        password_entered = request.form.get('password')
        if not username_entered or not password_entered:
            flash('Please enter a valid username and password', 'error')
            return render_template('login.html')

        # check password against this username's user record in database
        if this_user_in_db:
            if check_password_hash(this_user_in_db['password'],
                                   form['password']):
                if form['password'] == form['password1']:
                    # once verified with user record in database,
                    # start a new session and redirect to main recipelist
                    session['user'] = username_entered
                    flash('You have successfully logged in', 'success')
                    return redirect(url_for('recipelist'))
        else:
            # else if password does not match, flash error message
            flash('The password did not match the user profile', 'error')
            return render_template('login.html')

    if g.user:
        return redirect(url_for('recipelist'))

    return render_template('login.html')

    # Begin creating new_user dict for possible insertion to database
    # new_user = {}
    # new_user['username'] = request.form.get('username')
    # new_user['email'] = request.form.get('email')
    # Once all required field are populated without error above,
    # insert new user into database and redirect to login page
    # if new_user['username'] and new_user['email'] and new_user['password']:
    # new_user['liked_recipes'] = []
    # db.users.insert_one(new_user)
    # flash('You have successfully signed up, you can now log in', 'success')
    # return redirect(url_for('home'))
    # return render_template('signup.html')


@app.route('/logout')
def logout():
    # remove the user and user_id from the session if it's there
    session.pop('user', None)
    flash('You have successfully logged out', 'success')
    return redirect(url_for('home'))


@app.route('/recipelist')
def recipelist():
    cuisines = mongo.db.cuisines
    recipes = mongo.db.recipes
    cuisines = list(cuisines.find().sort('cuisine_name', 1))
    recipes = list(recipes.find())

    for arg in request.args:
        if 'recipe_search' in arg:
            new_recipe_list = []
            query = request.args['recipe_search']
            for recipe in recipes:
                if recipe['recipe_name'].lower().find(query.lower()) != -1:
                    new_recipe_list.append(recipe)
            return render_template('recipelist.html', recipes=new_recipe_list,
                                   cuisines=cuisines, user=g.user)

        elif 'cuisine_select' in arg:
            new_recipe_list = []
            query = request.args['cuisine_select']
            for recipe in recipes:
                if recipe['cuisine'] == query:
                    new_recipe_list.append(recipe)
            return render_template('recipelist.html', recipes=new_recipe_list,
                                   cuisines=cuisines, user=g.user)

        elif 'sort' in arg:
            if request.args['sort'] == 'votes':
                new_recipe_list = list(mongo.db.recipes.find().sort('upvotes', -1))
                return render_template('recipelist.html',
                                       recipes=new_recipe_list,
                                       cuisines=cuisines, user=g.user)
            elif request.args['sort'] == 'asc':
                new_recipe_list = list(mongo.db.recipes.find().sort('recipe_name', 1))
                return render_template('recipelist.html',
                                       recipes=new_recipe_list,
                                       cuisines=cuisines,
                                       user=g.user)
            elif request.args['sort'] == 'dsc':
                new_recipe_list = list(mongo.db.recipes.find().sort('recipe_name', -1))
                return render_template('recipelist.html',
                                       recipes=new_recipe_list,
                                       cuisines=cuisines, user=g.user)

    return render_template('recipelist.html', recipes=recipes,
                           cuisines=cuisines, user=g.user)


@app.route('/recipe/<recipe_id>/')
def recipe(recipe_id):
    this_recipe = recipes.find_one({'_id': ObjectId(recipe_id)})
    recipe_id = str(this_recipe['_id'])
    allergens = list(mongo.db.allergens.find())
    return render_template('recipe.html', recipe=this_recipe,
                           allergens=allergens, user=g.user,
                           recipe_id=recipe_id)


@app.route('/add_like/<recipe_id>/<user>/', methods=['POST'])
def add_like(recipe_id, user):

    # update liked_by list in recipe
    this_recipe = recipes.find_one({'_id': ObjectId(recipe_id)})
    liked_by = list(this_recipe['liked_by'])
    if user not in liked_by:
        liked_by.append(user)
    this_recipe['liked_by'] = liked_by
    this_recipe['upvotes'] = len(liked_by)
    recipes.update_one({'_id': ObjectId(recipe_id)}, {'$set': this_recipe})

    # update liked_recipes list in user
    this_user = users.find_one({'username': user})
    liked_recipes = list(this_user['liked_recipes'])
    if recipe_id not in liked_recipes:
        liked_recipes.append(recipe_id)
    this_user['liked_recipes'] = liked_recipes
    users.update_one({'username': user}, {'$set': this_user})

    return "Recipe Liked by User"


@app.route('/remove_like/<recipe_id>/<user>/', methods=['POST'])
def remove_like(recipe_id, user):

    # update liked_by list in recipe
    this_recipe = recipes.find_one({'_id': ObjectId(recipe_id)})
    liked_by = list(this_recipe['liked_by'])
    if user in liked_by:
        liked_by.remove(user)
    this_recipe['liked_by'] = liked_by
    this_recipe['upvotes'] = len(liked_by)
    recipes.update_one({'_id': ObjectId(recipe_id)}, {'$set': this_recipe})

    # update liked_recipes list in user
    this_user = users.find_one({'username': user})
    liked_recipes = list(this_user['liked_recipes'])
    if recipe_id in liked_recipes:
        liked_recipes.remove(recipe_id)
    this_user['liked_recipes'] = liked_recipes
    users.update_one({'username': user}, {'$set': this_user})

    return "Recipe Un-Liked by User"


@app.route('/add_recipe')
def add_recipe():
    allergens = mongo.db.allergens
    ingredients = mongo.db.ingredients
    cuisines = mongo.db.cuisines
    cuisines = list(cuisines.find().sort('cuisine_name', 1))
    ingredients = list(ingredients.find().sort('ingredient_name', 1))
    allergens = list(allergens.find())
    return render_template('add_recipe.html', cuisines=cuisines,
                           ingredients=ingredients, allergens=allergens,
                           user=g.user)


@app.route('/edit_recipe/<recipe_id>/')
def edit_recipe(recipe_id):
    cuisines = mongo.db.cuisines
    allergens = mongo.db.allergens
    ingredients = mongo.db.ingredients
    cuisines = list(cuisines.find().sort('cuisine_name', 1))
    ingredients = list(ingredients.find().sort('ingredient_name', 1))
    allergens = list(allergens.find())
    this_recipe = recipes.find_one({'_id': ObjectId(recipe_id)})
    return render_template('edit_recipe.html', cuisines=cuisines,
                           ingredients=ingredients, allergens=allergens,
                           recipe=this_recipe, user=g.user)


@app.route('/update_recipe/<recipe_id>', methods=["POST"])
def update_recipe(recipe_id):

    # organise method steps from form and build
    # new ordered array containing them
    step_keys = []
    method_steps = []
    for stepkey in request.form.to_dict():
        if 'step' in stepkey:
            step_keys.append(stepkey)
    for i in range(1, len(step_keys) + 1):
        method_steps.append(request.form.get('step-' + str(i)))

    # organise ingredients from form and build new 2D containing
    # qty-ingredient pairs
    ingredients_arr = []
    qty_arr = []
    ing_arr = []
    for ing_key in request.form.to_dict():
        if 'ingredient-qty-' in ing_key:
            qty_arr.append(ing_key)
        if 'ingredient-name-' in ing_key:
            ing_arr.append(ing_key)
    for i in range(1, len(qty_arr) + 1):
        qty = request.form.get('ingredient-qty-' + str(i))
        ing = request.form.get('ingredient-name-' + str(i))
        ingredients_arr.append([qty, ing])

    # find selected allergens and form new array containing them
    allergens = mongo.db.allergens.find()
    allergen_arr = []
    for allergen in list(allergens):
        for key in request.form.to_dict():
            if key == allergen['allergen_name']:
                allergen_arr.append(key)

    # create new document that will be used as the update
    # dict to update database
    updated_recipe = {}
    updated_recipe['recipe_name'] = request.form.get('recipe_name')
    updated_recipe['ingredients'] = ingredients_arr
    updated_recipe['method'] = method_steps
    updated_recipe['allergens'] = allergen_arr
    updated_recipe['cuisine'] = request.form.get('cuisine')
    if request.form.get('image_url') == "":
        updated_recipe['image_url'] = placeholder_image
    else:
        updated_recipe['image_url'] = request.form.get('image_url')
    recipes.update_one({'_id': ObjectId(recipe_id)}, {'$set': updated_recipe})

    return redirect(url_for('recipelist'))


@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    recipes.delete_one({'_id': ObjectId(recipe_id)})
    flash('Recipe successfully deleted', 'success')
    return redirect(url_for('recipelist'))


@app.route('/insert_recipe', methods=['POST'])
def insert_recipe():

    # organise method steps from form and build
    # new ordered array containing them
    step_keys = []
    method_steps = []
    for stepkey in request.form.to_dict():
        step_keys.append(stepkey)
    for i in range(1, len(step_keys) + 1):
        method_steps.append(request.form.get('step-' + str(i)))

    # organise ingredients from form and build
    # new 2D containing qty-ingredient pairs
    ingredients_arr = []
    qty_arr = []
    ing_arr = []
    for ing_key in request.form.to_dict():
        if 'ingredient-qty-' in ing_key:
            qty_arr.append(ing_key)
        if 'ingredient-name-' in ing_key:
            ing_arr.append(ing_key)
    for i in range(1, len(qty_arr) + 1):
        qty = request.form.get('ingredient-qty-' + str(i))
        ing = request.form.get('ingredient-name-' + str(i))
        ingredients_arr.append([qty, ing])

    # find selected allergens and form new array containing them
    allergens = mongo.db.allergens.find()
    # allergens = allergens.find()
    allergen_arr = []
    for allergens in list(allergens):
        for key in request.form.to_dict():
                allergen_arr.append(key)

    # create new database document and insert it to database
    new_recipe = {}
    new_recipe['recipe_name'] = request.form.get('recipe_name')
    new_recipe['ingredients'] = ingredients_arr
    new_recipe['method'] = method_steps
    new_recipe['allergens'] = allergen_arr
    new_recipe['liked_by'] = []
    new_recipe['author'] = session['user']
    new_recipe['cuisine'] = request.form.get('cuisine')
    if request.form.get('image_url') == "":
        new_recipe['image_url'] = placeholder_image
    else:
        new_recipe['image_url'] = request.form.get('image_url')
    recipes.insert_one(new_recipe)
    flash('Recipe successfully created', 'success')
    return redirect(url_for('recipelist'))

# My recipes
@app.route('/my_recipes')
def my_recipes():
   
    return render_template("my_recipes.html")

# Account Settings
@app.route("/account_settings")
def account_settings():
    
    return render_template('account_settings.html')



# Error Handling
# @app.errorhandler(404)
# def page_not_found(error):
#     return render_template('404.html'), 404

# @app.errorhandler(500)
# def something_wrong(error):
#     return render_template('500.html'), 500


# run application
if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)