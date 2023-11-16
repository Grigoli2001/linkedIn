from flask import Blueprint, render_template,url_for,session,redirect, current_app
import os
import sqlite3
from werkzeug.utils import secure_filename

from ..root import conn_db
from .forms import RegistrationForm
from .login import login_logic
from flask_login import current_user
register = Blueprint('register',__name__)


@register.route('/', methods = ['GET','POST'])
def add_user_form():
    form = RegistrationForm()
    if form.validate_on_submit():
        employer = form.employer.data
        email = form.email.data.lower()
        password = form.password.data
        profile_pic = form.profile_pic.data
        fullname = form.fullname.data
        if profile_pic:
            profile_pic_filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], profile_pic_filename)
            profile_pic.save(profile_pic_path)
            
            # Save the image path in the database
            profile_pic_db_path = os.path.join('static', 'uploads', profile_pic_filename)  # Relative path for HTML
        else:
            profile_pic_db_path = None  # Handle the case where no image was uploaded
        try:
            db = conn_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO users (employer, email, password,profile_pic_path,fullname) VALUES (?, ?, ?,?,?)', (employer, email, password,profile_pic_db_path,fullname))
            db.commit()
            user = login_logic(email, password)
            if user:
                return redirect(url_for('root.home'))
        except Exception as e:
            print(e)
            return render_template('register.html',reg_form = form, error = str(e))
    return render_template('register.html',reg_form = form)






