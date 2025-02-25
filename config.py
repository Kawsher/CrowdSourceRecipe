import os

SECRET_KEY = "supersecretkey"
MONGO_URI = "mongodb://localhost:27017/crowd_recipe_db"

# File upload settings
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
