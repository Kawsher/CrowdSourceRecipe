import os
import certifi
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from flask import request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Use a strong secret in production!

# Use your MongoDB Atlas connection string and specify the database name.
app.config['MONGO_URI'] = (
    "mongodb+srv://kawsher11:mahbub960@cluster0.fysvg.mongodb.net/crowd_recipe_db?"
    "retryWrites=true&w=majority&appName=Cluster0"
)

# Pass the CA file to PyMongo to help verify the SSL certificate
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Helper decorator to require login for protected routes.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Landing page route: if logged in, redirect to home, else show welcome page.
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

# Define upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form fields
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        full_name = request.form.get('full_name').strip()
        bio = request.form.get('bio').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate that the passwords match
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('signup'))
        
        # Validate uniqueness: check if username or email already exists
        existing_user = mongo.db.users.find_one({
            "$or": [{"username": username}, {"email": email}]
        })
        if existing_user:
            flash("Username or email already exists.")
            return redirect(url_for('signup'))
        
        # Process the profile picture upload
        profile_pic = request.files.get('profile_pic')
        profile_pic_filename = None
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            # Save the file to the upload folder
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Store the relative path (or filename) in the database
            profile_pic_filename = os.path.join("uploads", filename)
        
        # Hash the password for security
        hashed_password = generate_password_hash(password)
        
        # Create the user document including all required fields
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "bio": bio,
            "password": hashed_password,
            "profile_pic": profile_pic_filename  # This can be None if no file was uploaded
        }
        
        try:
            result = mongo.db.users.insert_one(user_data)
            print("Inserted ID:", result.inserted_id)
            flash("Signup successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            print("Error inserting document:", e)
            flash("There was an error processing your signup.")
            return redirect(url_for('signup'))
    
    # For GET requests, simply render the signup form
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = mongo.db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('You have been logged in!')
            return redirect(url_for('home'))  # Redirect to home page after successful login
        
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    
    return render_template('login.html')

# Logout route.
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

# Protected home page route: displays posted recipes.
@app.route('/home')
@login_required
def home():
    recipes = mongo.db.recipes.find()
    return render_template('home.html', recipes=recipes)

# Route to post a new recipe.
@app.route('/post_recipe', methods=['GET', 'POST'])
@login_required
def post_recipe():
    if request.method == 'POST':
        recipe_title = request.form.get('title').strip()
        recipe_description = request.form.get('description').strip()
        recipe_ingredients = request.form.get('ingredients').strip()
        recipe_instructions = request.form.get('instructions').strip()
        
        recipe_data = {
            'title': recipe_title,
            'description': recipe_description,
            'ingredients': recipe_ingredients,
            'instructions': recipe_instructions,
            'posted_by': session['username']
        }
        mongo.db.recipes.insert_one(recipe_data)
        flash('Recipe posted successfully!')
        return redirect(url_for('home'))
    
    return render_template('post_recipe.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
