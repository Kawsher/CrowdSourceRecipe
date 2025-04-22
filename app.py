import os
import certifi
from flask import Flask, render_template, request, session,redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bson import ObjectId
import re
from fractions import Fraction
from fractions import Fraction
from flask import jsonify, request
from bson import ObjectId
import re
import datetime


app = Flask(__name__)
app.secret_key = 'crowdrecipe@1233'

# Load additional config from config.py if available
app.config.from_object('config')

# Set MongoDB URI (update with your credentials if needed)
app.config['MONGO_URI'] = (
    "mongodb+srv://kawsher11:mahbub960@cluster0.fysvg.mongodb.net/crowd_recipe_db?"
    "retryWrites=true&w=majority&appName=Cluster0"
)

# Define allowed file extensions (for uploads)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Define upload folder and ensure it exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize extensions
mongo = PyMongo(app, tlsCAFile=certifi.where())
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, password, saved_recipes=None):
        self.id = user_id  # id must be a string
        self.username = username
        self.password = password
        self.saved_recipes = saved_recipes if saved_recipes is not None else []


# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(
            user_id=str(user_data["_id"]),
            username=user_data["username"],
            password=user_data["password"],
            saved_recipes=[str(recipe_id) for recipe_id in user_data.get('saved_recipes', [])],
        )
    return None

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Landing page route: if logged in, redirect to home; else show index page.
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        full_name = request.form.get('full_name').strip()
        bio = request.form.get('bio').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('signup'))

        # Check if username or email already exists
        existing_user = mongo.db.users.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            flash("Username or email already exists.")
            return redirect(url_for('signup'))

        # Process profile picture upload if provided
        profile_pic = request.files.get('profile_pic')
        profile_pic_filename = None
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_pic_filename = os.path.join("uploads", filename)

        hashed_password = generate_password_hash(password)
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "bio": bio,
            "password": hashed_password,
            "profile_pic": profile_pic_filename,
            "saved_recipes": []  # Initialize saved_recipes
        }
        try:
            mongo.db.users.insert_one(user_data)
            #flash("Signup successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            print("Error inserting document:", e)
            #flash("There was an error processing your signup.")
            return redirect(url_for('signup'))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user_data = mongo.db.users.find_one({'username': username})

        # Check if user exists and password is correct
        if user_data and check_password_hash(user_data['password'], password):
            user_instance = User(
                user_id=str(user_data["_id"]),
                username=user_data["username"],
                password=user_data["password"],
                saved_recipes=[str(recipe_id) for recipe_id in user_data.get('saved_recipes', [])],
            )
            login_user(user_instance)
            return redirect(url_for('home'))  # Redirect to home after successful login

        #flash('Invalid username or password.', 'error')
        return redirect(url_for('login'))  # Redirect to login page if login fails

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Home route: displays recipes and a welcome message.
@app.route('/home', methods=['GET'])
@login_required
def home():
    search_term = request.args.get('search', '').strip()
    min_rating = request.args.get('min_rating', None)

    if search_term:
        recipes_cursor = mongo.db.recipes.find({
            "$or": [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"ingredients": {"$regex": search_term, "$options": "i"}}
            ]
        }).sort("_id", -1)
    else:
        recipes_cursor = mongo.db.recipes.find().sort("_id", -1)

    recipes = list(recipes_cursor)
    for recipe in recipes:
        if 'ratings' in recipe and len(recipe['ratings']) > 0:
            recipe['average_rating'] = sum(recipe['ratings']) / len(recipe['ratings'])
        else:
            recipe['average_rating'] = 0

    if min_rating:
        min_rating = int(min_rating)
        recipes = [r for r in recipes if r['average_rating'] >= min_rating]
        if min_rating == 5:
            recipes = [r for r in recipes if r['average_rating'] == 5]

    return render_template('home.html', recipes=recipes, username=current_user.username)



# Route to post a new recipe.
@app.route('/post_recipe', methods=['GET', 'POST'])
@login_required
def post_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        cuisine = request.form.get('cuisine')
        meal=request.form.get('meal')
        # Get HealthyDiet as a string, then split into a list if not empty
        healthy_diet_str = request.form.get('HealthyDiet', "")
        healthy_diet = healthy_diet_str.split(',') if healthy_diet_str else []
        
        picture_filename = None
        if 'picture' in request.files:
            picture = request.files['picture']
            if picture and allowed_file(picture.filename):
                filename = secure_filename(picture.filename)
                picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                picture_filename = filename
        
        # Adding the link referenece (issue number 18)
        video_link = request.form.get('video_link')



        recipe_data = {
            "title": title,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "cuisine": cuisine,
            "HealthyDiet": healthy_diet,  # Store as list in MongoDB
            "meal":meal ,
            "picture": picture_filename,
            "video_link": video_link,
            "user_id": current_user.id
        }

        mongo.db.recipes.insert_one(recipe_data)
       # flash("Recipe posted successfully!", "success")
        return redirect(url_for('home'))

    return render_template('post_recipe.html')

# Route to rate a recipe.
@app.route('/rate_recipe', methods=['POST'])
@login_required
def rate_recipe():
    data = request.json
    if not data or "recipe_id" not in data or "rating" not in data:
        return jsonify({"success": False, "message": "Invalid request"}), 400

    recipe_id = data.get('recipe_id')

    try:
        rating = int(data.get('rating'))
        if not (1 <= rating <= 5):
            return jsonify({"success": False, "message": "Invalid rating value"}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Rating must be a number"}), 400

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})

    if recipe:
        mongo.db.recipes.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$push": {"ratings": rating}}  # Append rating to list
        )

        # Recalculate and update the average rating in DB
        updated_recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
        if 'ratings' in updated_recipe and len(updated_recipe['ratings']) > 0:
            avg_rating = round(sum(updated_recipe['ratings']) / len(updated_recipe['ratings']), 1)
        else:
            avg_rating = 0

        mongo.db.recipes.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$set": {"average_rating": avg_rating}}  # Store average rating
        )

        return jsonify({"success": True, "message": "Rating saved!", "average_rating": avg_rating})

    return jsonify({"success": False, "message": "Recipe not found"}), 404

@app.route('/high_rated_recipes', methods=['GET'])
@login_required
def high_rated_recipes():
    rating_filter = float(request.args.get('rating', 4.5))

    recipes_cursor = mongo.db.recipes.find()
    high_rated_recipes = []

    for recipe in recipes_cursor:
        if 'ratings' in recipe and len(recipe['ratings']) > 0:
            # Calculate the average rating
            average_rating = round(sum(recipe['ratings']) / len(recipe['ratings']), 1)

            # Check if the average rating is equal to the filter
            if average_rating == rating_filter:
                recipe['average_rating'] = average_rating
                high_rated_recipes.append(recipe)

    return render_template('high_rated_recipes.html',
                           recipes=high_rated_recipes,
                           selected_rating=rating_filter)


from bson.objectid import ObjectId

@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        flash("Recipe not found", "error")
        return redirect(url_for('home'))

    # Fetch all reviews related to this recipe
    reviews = list(mongo.db.reviews.find({"recipe_id": recipe_id}))
    avg_rating = recipe.get("average_rating", 0)

    return render_template("recipe_detail.html", recipe=recipe, reviews=reviews,avg_rating=avg_rating)


@app.route('/add_review/<recipe_id>', methods=['POST'])
@login_required
def add_review(recipe_id):
    review_text = request.form.get('review_text')
    if review_text:
        review = {
            'text': review_text,
            'author': current_user.username,
            'recipe_id': recipe_id
        }
        mongo.db.reviews.insert_one(review)
        return jsonify({'success': True, 'review': review})
    return jsonify({'success': False, 'message': 'Review text is required'}), 400


@app.route('/recipe/<recipe_id>/scale', methods=['GET'])
def scale_ingredients(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        return jsonify({'success': False, 'message': 'Recipe not found.'})

    scale = float(request.args.get('scale', 1))
    ingredients_string = recipe.get('ingredients', '')
    ingredients = [ing.strip() for ing in ingredients_string.splitlines()]
    scaled_ingredients = []

    for ingredient in ingredients:
        # Updated regex to handle ranges with spaces and different number formats
        match = re.match(r'^((\d+\s*-\s*\d+)|(\d+\s+\d+[/⁄]\d+)|(\d+[/⁄]\d+)|(\d+\.\d+)|(\d+))\s*', ingredient)
        if not match:
            scaled_ingredients.append(ingredient)
            continue

        quantity_str = match.group(1).replace('⁄', '/').strip()  # Normalize Unicode
        rest = ingredient[len(match.group(0)):].lstrip()

        if '-' in quantity_str:  # Handle ranges
            low, high = [s.strip() for s in quantity_str.split('-', 1)]
            low_num = parse_number(low)
            high_num = parse_number(high)
            
            scaled_low = low_num * scale
            scaled_high = high_num * scale
            
            scaled_str = f"{simplify_quantity(scaled_low)}-{simplify_quantity(scaled_high)}"
        else:  # Handle single quantities
            quantity = parse_number(quantity_str)
            scaled_quantity = quantity * scale
            scaled_str = simplify_quantity(scaled_quantity)

        scaled_ingredients.append(f"{scaled_str} {rest}" if rest else scaled_str)

    return jsonify({'success': True, 'ingredients': scaled_ingredients})

def parse_number(num_str):
    """Convert string to float, handling fractions and mixed numbers"""
    if ' ' in num_str and '/' in num_str:
        whole, fraction = num_str.split(' ', 1)
        return float(whole) + float(Fraction(fraction))
    elif '/' in num_str:
        return float(Fraction(num_str))
    return float(num_str)

def simplify_quantity(value):
    """Convert float to simplified fraction or mixed number"""
    if value.is_integer():
        return str(int(value))
    
    frac = Fraction(value).limit_denominator(8)
    if frac.numerator > frac.denominator:
        whole = frac.numerator // frac.denominator
        remainder = frac.numerator % frac.denominator
        if remainder == 0:
            return str(whole)
        return f"{whole} {Fraction(remainder, frac.denominator)}"
    return str(frac)

#Route to display favorite recipes.
@app.route('/favourite_recipes', methods=['GET'])
@login_required
def favourite_recipes():
    recipe_ids = [ObjectId(recipe_id) for recipe_id in current_user.saved_recipes]
    favorite_recipes = list(
        mongo.db.recipes.find({"_id": {"$in": recipe_ids}}).sort("_id", -1)
    )
    return render_template('home.html', recipes=favorite_recipes)


# Route to save a recipe as a favorite.
@app.route('/save_recipe/<recipe_id>', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if recipe:
        # Add the recipe to the user's saved recipes if not already saved
        existing_save = mongo.db.users.find_one(
            {"_id": ObjectId(current_user.id), "saved_recipes": ObjectId(recipe_id)}
        )
        if not existing_save:
            mongo.db.users.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$addToSet": {"saved_recipes": ObjectId(recipe_id)}}
            )
            flash("Recipe saved successfully!", "success")
            return redirect(request.referrer or url_for('home'))
        else:
            flash("Recipe already saved.", "info")
            return redirect(request.referrer or url_for('home'))
    else:
        flash("Recipe not found.", "error")
        return redirect(request.referrer or url_for('home'))
    
@app.route('/cuisine/<cuisine>')
def filter_by_cuisine(cuisine):
    if cuisine.lower() == 'all':
        filtered_recipes = list(mongo.db.recipes.find().sort("_id", -1))
    else:
        filtered_recipes = list(
            mongo.db.recipes.find({'cuisine': {'$regex': cuisine, '$options': 'i'}}).sort("_id", -1)
        )
    return render_template('home.html', recipes=filtered_recipes, selected_cuisine=cuisine)

@app.route('/healthy_diet/<healthy_diet>')
@login_required
def filter_by_healthy_diet(healthy_diet):
    filtered_recipes = list(
        mongo.db.recipes.find({'HealthyDiet': healthy_diet}).sort("_id", -1)
    )
    return render_template('home.html', recipes=filtered_recipes, username=current_user.username)


@app.route('/meal_type/<meal_type>')
@login_required
def filter_by_meal_type(meal_type):
    filtered_recipes = list(
        mongo.db.recipes.find({'meal': meal_type}).sort("_id", -1)
    )
    return render_template('home.html', recipes=filtered_recipes, username=current_user.username)

# Filter recipes by category and rating
@app.route('/filter_by_popular', methods=['GET'])
def filter_by_popular():
    category = request.args.get('popular')
    min_rating = 4.5
    if not category:
        flash("No category specified.", "error")
        return redirect(url_for('home'))

    recipes_cursor = mongo.db.recipes.find({
        "meal": category,
        "average_rating": {"$gte": min_rating}
    }).sort("_id", -1)

    recipes = list(recipes_cursor)
    return render_template('home.html', recipes=recipes,
                           username=current_user.username if current_user.is_authenticated else None)

@app.route('/filter_by_popular/<category>', methods=['GET'])
def filter_by_popular_category(category):
    min_rating = 4.5
    recipes_cursor = mongo.db.recipes.find({
        "meal": category,
        "average_rating": {"$gte": min_rating}
    }).sort("_id", -1)

    recipes = list(recipes_cursor)
    return render_template('home.html', recipes=recipes,
                           username=current_user.username if current_user.is_authenticated else None)
                           
@app.route('/high_by_popular')
def high_by_popular():
    rating = request.args.get('rating', type=float)
    if rating is None:
        flash("No rating specified.", "error")
        return redirect(url_for('home'))

    recipes_cursor = mongo.db.recipes.find({
        "average_rating": rating
    }).sort("_id", -1)

    recipes = list(recipes_cursor)
    return render_template('home.html', recipes=recipes,
                           username=current_user.username if current_user.is_authenticated else None)


@app.route('/add_reply', methods=['POST'])
@login_required
def add_reply():
    data = request.json
    review_id = data.get('review_id')
    recipe_id = data.get('recipe_id')
    reply_text = data.get('reply_text')
    
    if not all([review_id, recipe_id, reply_text]):
        return jsonify({'success': False, 'message': 'Missing required data'}), 400
    
    # Create the reply object
    reply = {
        'text': reply_text,
        'author': current_user.username,
        'created_at': datetime.datetime.now()
    }
    
    # Update the review document by adding the reply to its replies array
    result = mongo.db.reviews.update_one(
        {'_id': ObjectId(review_id)},
        {'$push': {'replies': reply}}
    )
    
    if result.modified_count > 0:
        return jsonify({
            'success': True,
            'reply': reply
        })
    else:
        return jsonify({'success': False, 'message': 'Could not add reply'}), 500
    
# Profile page route - displays user info and posted recipes
@app.route('/profile', methods=['GET'])
@login_required
def profile():
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    user_recipes = list(
        mongo.db.recipes.find({"user_id": current_user.id}).sort("_id", -1)
    )

    for recipe in user_recipes:
        if 'ratings' in recipe and len(recipe['ratings']) > 0:
            recipe['average_rating'] = sum(recipe['ratings']) / len(recipe['ratings'])
        else:
            recipe['average_rating'] = 0

    return render_template('profile.html', user=user_data, recipes=user_recipes)


# Change password route
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    confirm_password = request.form.get('confirmPassword')
    
    # Get current user data
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    
    # Validate form data
    if not all([current_password, new_password, confirm_password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "New passwords do not match"}), 400
        
    if len(new_password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters long"}), 400
    
    # Verify current password
    if not check_password_hash(user_data['password'], current_password):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
    
    # Hash new password and update in database
    hashed_password = generate_password_hash(new_password)
    mongo.db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"password": hashed_password}}
    )
    
    return jsonify({"success": True, "message": "Password changed successfully"})



# Delete recipe route
@app.route('/delete_recipe/<recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    try:
        # Find the recipe
        recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
        
        # Check if recipe exists and belongs to current user
        if not recipe:
            return jsonify({"success": False, "message": "Recipe not found"}), 404
            
        if recipe.get('user_id') != current_user.id:
            return jsonify({"success": False, "message": "Unauthorized to delete this recipe"}), 403
        
        # Delete the recipe
        mongo.db.recipes.delete_one({"_id": ObjectId(recipe_id)})
        
        # Also delete associated reviews
        mongo.db.reviews.delete_many({"recipe_id": recipe_id})
        
        return jsonify({"success": True, "message": "Recipe deleted successfully"})
    except Exception as e:
        print(f"Error deleting recipe: {e}")
        return jsonify({"success": False, "message": "Error deleting recipe"}), 500



# Edit user profile route
@app.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    try:
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        bio = request.form.get('bio')
        
        # Check if username already exists (if it's being changed)
        current_user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        if username != current_user_data.get('username'):
            existing_user = mongo.db.users.find_one({"username": username})
            if existing_user:
                return jsonify({"success": False, "message": "Username already exists"}), 400
        
        # Process profile picture if provided
        profile_pic_filename = current_user_data.get('profile_pic')
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic and profile_pic.filename != '' and allowed_file(profile_pic.filename):
                filename = secure_filename(profile_pic.filename)
                profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_pic_filename = os.path.join("uploads", filename)
        
        # Update user data
        mongo.db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {
                "username": username,
                "email": email,
                "full_name": full_name,
                "bio": bio,
                "profile_pic": profile_pic_filename
            }}
        )
        
        return jsonify({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({"success": False, "message": "Error updating profile"}), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8925)

