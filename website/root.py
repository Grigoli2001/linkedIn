import os
from flask import Blueprint, render_template,url_for, jsonify,g, request, redirect, flash, current_app
import sqlite3
from flask_login import login_required,current_user,logout_user
from .APIs.forms import LoginForm , PostForm
from .APIs.mongoDB import client
from datetime import datetime

from werkzeug.utils import secure_filename

from bson import ObjectId

# from .login import User
root = Blueprint('root',__name__)

@root.route('/')
def index():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("root.home"))
    return render_template('welcome.html',form = form)

def conn_db():
    db = getattr(g,'_database',None)
    if db is None:
        db = g._database = sqlite3.connect('user_data.db')
        create_user_table(db)
    
    return db
        
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create a table if it doesn't exist
def create_user_table(db):
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password text NOT NULL,
            profile_pic_path text,
            fullname text
        )
    ''')
    db.commit()

@root.route('/users')
def show_users():
    # Fetch all user data from the database
    db = conn_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    # Pass the user data to the template
    return jsonify(users)

def get_user_info_by_id(user_id):
    conn = conn_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if user:   
        return user
    return None


@root.route('/home')
@login_required
def home():
    form = PostForm()
    db = client['linkedIn']
    collection = db['tweets']
    tweets = list(collection.find())
    for tweet in tweets:
        tweet['_id'] = str(tweet['_id'])
        user_info = get_user_info_by_id(tweet['user_id'])
        if user_info:
            tweet['author_name'] = user_info[1]  # Access username using integer index
            tweet['author_profile_pic'] = user_info[4]  # Access profile_pic_path using integer index
            tweet['author_fullname'] = user_info[5]
        else:
            # Handle the case where the author was not found
            tweet['author_fullname'] = "Unknown"
            tweet['author_name'] = 'Unknown'
            tweet['author_profile_pic'] = None
    tweets.reverse()
    return render_template('home.html', tweets = tweets, form = form)



@root.route('/jobs')
@login_required
def jobs():
    db = client['linkedIn']
    collection = db['jobs']
    jobs = list(collection.find())
    for job in jobs:
        if current_user.id in job['saved_by']:
            job['saved'] = True
    return render_template('jobs.html',jobs = jobs)



@root.route('/save_item/<id>', methods=['GET','POST'])
@login_required
def save_item(id):
    db = client['linkedIn']
    jobs = db['jobs']
    user_id = current_user.id
    job_id = ObjectId(id)
    jobs.update_one({'_id' : job_id}, {'$push' : {'saved_by' : user_id}})
    return redirect(url_for('root.jobs'))

@root.route('/delete_item/<id>', methods=['GET','POST'])
@login_required
def delete_item(id):
    db = client['linkedIn']
    collection = db['my_items']
    jobs = db['jobs']
    try:
        object_id = ObjectId(id)
    except Exception as e:
        print(f"Invalid ObjectId: {e}")
    collection.delete_one({'_id' : object_id})
    jobs.update_one({'_id' : object_id}, {'$pull' : {'saved_by' : current_user.id}})
    return redirect(url_for('root.my_items'))

@root.route('/my_items')
@login_required
def my_items():
    db = client['linkedIn']
    collection = db['jobs']
    jobs = list(collection.find())
    saved = []
    for job in jobs:
        if current_user.id in job['saved_by']:
            saved.append(job)
    return render_template('my_items.html',jobs = saved)
@root.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('root.index'))



@root.route('/add_tweet', methods=[ 'GET','POST'])
@login_required
def addTweet():
    db = client['linkedIn']
    collection = db['tweets']
    form = PostForm()  # Create an instance of the TweetForm
    if request.method == 'POST':     
        print("submited")   
        user_id = current_user.id
        content = form.content.data
        # Get the current timestamp
        created_at = datetime.now().isoformat()

        image = form.media.data  # Get the uploaded image
        if not content.strip() and not image:
            flash('Please provide either content or an image.', 'danger')
            return redirect(url_for('root.home'))
        # Check if an image was uploaded
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            
            # Save the image path in the database
            image_db_path = os.path.join('static', 'uploads', image_filename)  # Relative path for HTML
        else:
            image_db_path = None  # Handle the case where no image was uploaded
        
        tweet = {
            'user_id': user_id,
            'content': content,
            'created_at': created_at,
            'updated_at': None,
            'image_path': image_db_path  # Save the image path in the database
        }
        collection.insert_one(tweet)

        return redirect(url_for('root.home'))

    return redirect(url_for('root.home'))
  

@root.route('/delete_tweet/<id>')
@login_required
def delete_tweet(id):
    db = client['linkedIn']
    collection = db['tweets']
    try:
        object_id = ObjectId(id)
    except Exception as e:
        print(f"Invalid ObjectId: {e}")
    collection.delete_one({'_id' : object_id})
    return redirect(url_for('root.home'))

# to do 
# add a route to edit a tweet
@root.route('/edit_tweet/<id>', methods=['GET','POST'])
@login_required
def edit_tweet(id):
    pass


@root.route('/apply_job' , methods=['GET','POST'])
@login_required
def apply_job():
    db = client['linkedIn']
    collection = db['applications']
    if request.method == 'POST':
        form = request.form
        job_id = form['job_id']
        fullname = form['fullname']
        email = form['email'].lower() 
        resume = request.files['resume']
        phone_number = form['phone_number'].strip()
        cover_letter = form['cover_letter'] 
        if resume:
            resume_name = secure_filename(resume.filename)
            resume_path = os.path.join(current_app.config['APPLICATION_FOLDER'], resume_name)
            resume.save(resume_path)
            
            # Save the image path in the database
            resume_db_path = os.path.join('static', 'uploads', resume_name)  # Relative path for HTML
        else:
            resume_db_path = None  # Handle the case where no image was uploaded
        user_id = current_user.id
        job = {
            'job_id' : job_id,
            'fullname' : fullname,
            'email' : email,
            'resume' : resume_db_path,
            'phone_number' : phone_number,
            'cover_letter' : cover_letter,

        }
        applied = {
            'user_id' : user_id,
            'jobs_applied' : [job]
        }

        if collection.find_one({'user_id' : user_id}):
            collection.update_one({'user_id' : user_id}, {'$push' : {'jobs_applied' : job}})
        else:
            collection.insert_one(applied)
        return redirect(url_for('root.jobs'))