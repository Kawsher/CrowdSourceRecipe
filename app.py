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
    def __init__(self, id, username, password):
        self.id = id  # id must be a string
        self.username = username
        self.password = password

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(id=str(user_data["_id"]), username=user_data["username"], password=user_data["password"])
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
            "profile_pic": profile_pic_filename
        }
        try:
            mongo.db.users.insert_one(user_data)
            flash("Signup successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            print("Error inserting document:", e)
            flash("There was an error processing your signup.")
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
            user_instance = User(id=str(user_data["_id"]), username=user_data["username"], password=user_data["password"])
            login_user(user_instance)
            return redirect(url_for('home'))  # Redirect to home after successful login
        
        flash('Invalid username or password.', 'error')
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

    # Perform search query if search_term is present
    if search_term:
        recipes_cursor = mongo.db.recipes.find({
            "$or": [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"ingredients": {"$regex": search_term, "$options": "i"}}
            ]
        })
    else:
        recipes_cursor = mongo.db.recipes.find()

    # Convert cursor to list
    recipes = list(recipes_cursor)

    # Calculate average rating for each recipe
    for recipe in recipes:
        if 'ratings' in recipe and len(recipe['ratings']) > 0:
            recipe['average_rating'] = sum(recipe['ratings']) / len(recipe['ratings'])
        else:
            recipe['average_rating'] = 0

    # Apply rating filter if 'min_rating' is specified
    if min_rating:
        min_rating = int(min_rating)

        # Filter recipes based on the rating ranges
        if min_rating == 1:
            recipes = [recipe for recipe in recipes if 1 <= recipe['average_rating'] < 2]
        elif min_rating == 2:
            recipes = [recipe for recipe in recipes if 2 <= recipe['average_rating'] < 3]
        elif min_rating == 3:
            recipes = [recipe for recipe in recipes if 3 <= recipe['average_rating'] < 4]
        elif min_rating == 4:
            recipes = [recipe for recipe in recipes if 4 <= recipe['average_rating'] < 5]
        elif min_rating == 5:
            recipes = [recipe for recipe in recipes if recipe['average_rating'] == 5]

    # Pass recipes and username to template
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

        picture_filename = None
        if 'picture' in request.files:
            picture = request.files['picture']
            if picture and allowed_file(picture.filename):
                filename = secure_filename(picture.filename)
                picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                picture_filename = filename
        
        recipe_data = {
            "title": title,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "picture": picture_filename,
            "user_id": current_user.id
        }
        mongo.db.recipes.insert_one(recipe_data)
        flash("Recipe posted successfully!", "success")
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
            {"$push": {"ratings": rating}}
        )
        return jsonify({"success": True, "message": "Rating saved!"})
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


@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    if not recipe:
        flash('Recipe not found', 'error')
        return redirect(url_for('home'))
    
    # Fetch reviews for this recipe
    reviews = list(mongo.db.reviews.find({'recipe_id': recipe_id}))
    
    return render_template('recipe_detail.html', recipe=recipe, reviews=reviews)

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
        # Use regex to find quantity at start of ingredient
        match = re.match(r'^(\d+/\d+|\d+\.\d+|\d+\s+\d+/\d+|\d+)\s*', ingredient)
        if not match:
            scaled_ingredients.append(ingredient)
            continue

        quantity_str = match.group(1)
        rest = ingredient[len(quantity_str):].lstrip()

        # Convert mixed numbers and fractions to float
        if ' ' in quantity_str:
            whole, fraction = quantity_str.split(' ', 1)
            whole = float(whole)
            fraction = float(Fraction(fraction))
            quantity = whole + fraction
        elif '/' in quantity_str:
            quantity = float(Fraction(quantity_str))
        else:
            quantity = float(quantity_str)

        scaled_quantity = quantity * scale

        # Convert back to fraction format if applicable
        if scaled_quantity.is_integer():
            scaled_str = str(int(scaled_quantity))
        else:
            # Try to convert to common fraction
            frac = Fraction(scaled_quantity).limit_denominator(8)
            if frac.denominator == 1:
                scaled_str = str(frac.numerator)
            else:
                scaled_str = f"{frac.numerator}/{frac.denominator}"
                # Handle mixed numbers
                if frac.numerator > frac.denominator:
                    whole = frac.numerator // frac.denominator
                    remainder = frac.numerator % frac.denominator
                    scaled_str = f"{whole} {remainder}/{frac.denominator}"

        scaled_ingredient = f"{scaled_str} {rest}"
        scaled_ingredients.append(scaled_ingredient)

    return jsonify({'success': True, 'ingredients': scaled_ingredients})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

