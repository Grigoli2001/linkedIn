from flask import Blueprint, render_template,url_for,session,redirect, request, flash
from flask_login import  UserMixin, login_user,login_required,logout_user,current_user
from ..root import conn_db
from .. import login_manager
from .forms import LoginForm
login_blueprint = Blueprint('login_blueprint',__name__)


class User(UserMixin):
    def __init__(self,id):
        self.id = id
        self.username = None
        self.email = None
        self.password = None    
        self.authenticated = False
        self.fullname = None
    def is_active(self):
         return self.is_active()
    def is_anonymous(self):
         return False
    def is_authenticated(self):
         return self.authenticated
    def is_active(self):
         return True
    def get_id(self):
         return self.id
    def __repr__(self):
        return '<User %r>' % (self.username)
    def get_cart(self):
        return self.cart



@login_manager.user_loader
def load_user(user_id):
     # Fetch user data from the database
    db = conn_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user is not None:  # Check if a user is found
        cur_user = User(id=user_id)
        cur_user.username = user[1]
        cur_user.email = user[2]
        cur_user.password = user[3]
        cur_user.fullname = user[4]
        return cur_user

    return None  # Return None if no user is found

@login_blueprint.route('/',methods = ['GET','POST'])
def login_logic(auth_email = None,auth_password = None):
    form = LoginForm()
    if current_user.is_authenticated:
         return redirect(url_for('root.home'))
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        db = conn_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?',(email,))
        user = cursor.fetchone()
        if user:
            Us = load_user(user[0])
            if  password == Us.password:
                login_user(Us)
                return redirect(url_for('root.home'))
            else:
                flash('Your password is incorrect','danger')
        else:
            flash("Check your email", 'danger')
    if auth_email and auth_password:
        db = conn_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?',(auth_email,))
        user = cursor.fetchone()
        if user:
            Us = load_user(user[0])
            if auth_email == Us.email and auth_password == Us.password:
                login_user(Us)
                return redirect(url_for('root.index'))
            else:
                flash('Login Failed check your username and password','danger')


    return render_template('login.html', form = form)
 
