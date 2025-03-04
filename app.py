import os
import certifi
from flask import Flask, render_template, request, session,redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bson import ObjectId

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
        
        if user_data and check_password_hash(user_data['password'], password):
            # Create a user instance and log them in with Flask-Login
            user_instance = User(id=str(user_data["_id"]), username=user_data["username"], password=user_data["password"])
            login_user(user_instance)
            flash('You have been logged in!')
            return redirect(url_for('home'))
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

# Home route: displays recipes and a welcome message.
@app.route('/home', methods=['GET'])
@login_required
def home():
    search_term = request.args.get('search', '').strip()
    if search_term:
        recipes_cursor = mongo.db.recipes.find({
            "$or": [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"ingredients": {"$regex": search_term, "$options": "i"}}
            ]
        })
    else:
        recipes_cursor = mongo.db.recipes.find()
    recipes = list(recipes_cursor)
    for recipe in recipes:
        if 'ratings' in recipe and len(recipe['ratings']) > 0:
            recipe['average_rating'] = sum(recipe['ratings']) / len(recipe['ratings'])
        else:
            recipe['average_rating'] = 0
    return render_template('home.html', recipes=recipes,username=current_user.username)

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
    # Retrieve recipes with an average rating of 4.5 or above
    recipes_cursor = mongo.db.recipes.find()
    high_rated_recipes = []
    
    for recipe in recipes_cursor:
        if 'ratings' in recipe and len(recipe['ratings']) > 0:
            average_rating = sum(recipe['ratings']) / len(recipe['ratings'])
            if average_rating >= 4.5:
                recipe['average_rating'] = average_rating
                high_rated_recipes.append(recipe)
    
    return render_template('high_rated_recipes.html', recipes=high_rated_recipes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
