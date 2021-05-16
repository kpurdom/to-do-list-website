from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email


##WTForm
class AddTask(FlaskForm):
    task = StringField("Task:", validators=[DataRequired()])
    submit = SubmitField("Add New Task")


class AddList(FlaskForm):
    list = StringField("List Name:", validators=[DataRequired()])
    submit = SubmitField("Add New List")


class RegisterForm(FlaskForm):
    name = StringField("Name:", validators=[DataRequired()])
    email = StringField("Email:", validators=[DataRequired(), Email("This field requires a valid email address")])
    password = PasswordField("Password:", validators=[DataRequired()])

    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), Email("This field requires a valid email address")])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")