import logging
import os
import sqlite3
import time
from datetime import datetime

from bson import ObjectId
from flask import (Blueprint, current_app, flash, g, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required, logout_user
from werkzeug.utils import secure_filename

from .APIs.forms import LoginForm, PostForm
from .APIs.mongoDB import client

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
            employer TEXT NOT NULL,
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
            if user_info[4]:
                tweet['author_profile_pic'] = user_info[4]  # Access profile_pic_path using integer index
            else:
                tweet['author_profile_pic'] = "https://static.vecteezy.com/system/resources/thumbnails/003/337/584/small/default-avatar-photo-placeholder-profile-icon-vector.jpg"
            tweet['author_fullname'] = user_info[5]
        else:
            # Handle the case where the author was not found
            tweet['author_fullname'] = "Unknown"
            tweet['author_name'] = 'Unknown'
            tweet['author_profile_pic'] = "https://static.vecteezy.com/system/resources/thumbnails/003/337/584/small/default-avatar-photo-placeholder-profile-icon-vector.jpg"
    tweets.reverse()
    return render_template('home.html', tweets = tweets, form = form)



@root.route('/jobs')
@login_required
def jobs():
    db = client['linkedIn']
    collection = db['jobs']
    my_applications = db['applications']
    jobs = list(collection.find())
    applications = my_applications.find_one({'user_id' : current_user.id})
    for job in jobs:
        if current_user.id in job['saved_by']:
            job['saved'] = True
        for application in applications['jobs_applied']:
            if str(job['_id']) == application['job_id']:
                job['applied'] = True
    jobs.reverse()
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
    return redirect(url_for('root.home'))



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
        logging.info("Submitted a tweet.")
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
    jobs = db['jobs']
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
        cur_job = jobs.find_one({'_id' : ObjectId(job_id)})
        job = {
            'job_id' : job_id,
            'fullname' : fullname,
            'email' : email,
            'resume' : resume_db_path,
            'phone_number' : phone_number,
            'cover_letter' : cover_letter,
            'applied_at' : datetime.now().isoformat(),
            'status' : 'pending',

        }
        applied = {
            'user_id' : user_id,
            'jobs_applied' : [job]
        }

        if collection.find_one({'user_id' : user_id}):
            collection.update_one({'user_id' : user_id}, {'$push' : {'jobs_applied' : job}})
        else:
            collection.insert_one(applied)
        # increment application count
        jobs.update_one({'_id' : ObjectId(job_id)}, {'$inc' : {'application_count' : 1}})
        jobs.update_one({'_id' : ObjectId(job_id)},{'$push' : {'applied_by' : current_user.id}})
        return redirect(url_for('root.jobs'))
    
    return redirect(url_for('root.jobs'))



# TO DO
@root.route('/my_applications')
@login_required
def my_applications():
    db = client['linkedIn']
    collection = db['applications']
    applications = collection.find_one({'user_id' : current_user.id})
    jobs = db['jobs']
    job_list = []
    try:
        for application in applications['jobs_applied']:
            job = jobs.find_one({'_id' : ObjectId(application['job_id'])})
            print(job)
            job['status'] = application['status']
            job_list.append(job)
    except Exception as e:
        print(e)
    return render_template('my_applications.html',jobs = job_list)


@root.route('/my_jobs')
@login_required
def my_jobs():
    db = client['linkedIn']
    collection = db['jobs']
    jobs = list(collection.find({'posted_by' : current_user.id}))
    return render_template('my_jobs.html',jobs = jobs)

@root.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@root.route('/add_job', methods=['GET','POST'])
@login_required
def add_job():
    db = client['linkedIn']
    collection = db['jobs']
    if request.method == 'POST':
        form = request.form
        title = form['title']
        description = form['description']
        company = form['company']
        job_type = form['job_type']
        location = form['location']
        salary = form['salary']
        deadline = form['deadline']
        process = form['process']
        requirements = form['requirements'].split(',')
        skills = form['skills'].split(',')
        category = form['category']
        contact = form['contact']
        job = {
            'job_title' : title,
            'job_description' : description,
            'company' : company,
            'job_type' : job_type,
            'location' : location,
            'salary' : salary,
            'application_deadline' : deadline,
            'application_process' : process,
            'job_requirements' : requirements,
            'desired_skills' : skills,
            'job_category' : category,
            'date_posted' : datetime.now().isoformat(),
            'job_status' : 'Open',
            'contact_information' : contact,
            'tags'  : [],
            'posted_by' : current_user.id,
            'application_count' : 0,
            'saved_by' : [],
            'logo':'https://picsum.photos/200?random=112',
        }
        collection.insert_one(job)
        return redirect(url_for('root.my_jobs'))
    return redirect(url_for('root.my_jobs'))


@root.route('/application/<job_id>')
@login_required
def application(job_id):
    db = client['linkedIn']
    collection = db['applications']
    job_col = db['jobs']
    job = job_col.find_one({'_id' : ObjectId(job_id)})
    applications = []
    for user in job['applied_by']:
        user_info = get_user_info_by_id(user)
        if user_info[4]:
            user_profile_pic = user_info[4]
        else:
            user_profile_pic = "https://static.vecteezy.com/system/resources/thumbnails/003/337/584/small/default-avatar-photo-placeholder-profile-icon-vector.jpg"
        application = collection.find_one({'user_id' : user})
        for job in application['jobs_applied']:
            if job['job_id'] == job_id:
                job['user_profile_pic'] = user_profile_pic
                applications.append(job)  
    return jsonify(applications)
