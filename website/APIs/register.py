from flask import Blueprint, render_template,url_for,session,redirect, current_app
import os
import sqlite3
from ..root import conn_db
from .forms import RegistrationForm
from .login import login_logic
from flask_login import current_user
register = Blueprint('register',__name__)

@register.route('/', methods = ['GET','POST'])
def add_user_form():
    if current_user.is_authenticated:
        return redirect(url_for('root.home'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data.lower()
        password = form.password.data
        fullname = form.fullname.data

        try:
            db = conn_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO users (username, email, password,fullname) VALUES (?,?,?,?)', (username, email, password,fullname))
            db.commit()
            user = login_logic(email, password)
            if user:
                return redirect(url_for('root.home'))
        except Exception as e:
            return render_template('register.html', form = form, error = str(e))
    return render_template('register.html',form = form)




