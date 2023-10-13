from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField,FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from flask_wtf.file import  FileAllowed


class RegistrationForm(FlaskForm):
    username=StringField("Username", validators=[DataRequired(),Length(min=2,max=20)])
    fullname=StringField("Fullname", validators=[DataRequired(),Length(min=2,max=20)])
    email=StringField("Email Address", validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Sign Up')

class TweetForm(FlaskForm):
    content = TextAreaField('Content', validators=[])
    image = FileField('Image')

class LoginForm(FlaskForm):
    email=StringField("Email Address", validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=6)])
    submit = SubmitField('Sign in')

class PostForm(FlaskForm):
    content = TextAreaField()
    media = FileField('Media')
    submit = SubmitField('POST')

