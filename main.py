from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import LoginForm, RegisterForm, AddTask, AddList
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap(app)

##CONNECT TO DB
uri = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    lists = relationship("Lists", back_populates="user_list")
    tasks = relationship("Tasks", back_populates="user_task")


class Lists(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user_list = relationship("User", back_populates="lists")
    list = db.Column(db.String(250), nullable=False)
    tasks = relationship("Tasks", back_populates="list_task", cascade="all, delete, delete-orphan")


class Tasks(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey("lists.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    list_task = relationship("Lists", back_populates="tasks")
    user_task = relationship("User", back_populates="tasks")
    task = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(250), nullable=False)


db.create_all()


@app.route('/', methods=["GET", "POST"])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('home'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('home'))
        else:
            login_user(user)
            return redirect(url_for('show_lists'))
    return render_template("index.html", form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('home'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("show_lists"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/user')
def show_lists():
    if not current_user.is_authenticated:
        flash("You need to login or register to comment.")
        return redirect(url_for("home"))
    user_lists = Lists.query.filter_by(user_id=current_user.id).all()
    return render_template("lists.html", lists=user_lists, current_user=current_user)


@app.route('/add_list', methods=["GET", "POST"])
def add_list():
    if not current_user.is_authenticated:
        flash("You need to login or register to comment.")
        return redirect(url_for("home"))
    form = AddList()
    if form.validate_on_submit():
        new_list = Lists(
            list=form.list.data,
            user_id=current_user.id,
        )
        db.session.add(new_list)
        db.session.commit()
        return redirect(url_for("show_lists"))
    return render_template("add_list.html", form=form, current_user=current_user)


@app.route("/delete_list/<int:list_id>")
def delete_list(list_id):
    list_to_delete = Lists.query.get(list_id)
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for('show_lists'))


@app.route('/list/<int:list_id>', methods=["GET", "POST"])
def show_tasks(list_id):

    list_tasks = Tasks.query.filter_by(list_id=list_id)
    parent_list = Lists.query.get(list_id)

    if not current_user.is_authenticated:
        flash("You need to login or register to comment.")
        return redirect(url_for("login"))

    return render_template("tasks.html", tasks=list_tasks, parent_list=parent_list, current_user=current_user)


@app.route('/<int:list_id>/add_task', methods=["GET", "POST"])
def add_task(list_id):
    if not current_user.is_authenticated:
        flash("You need to login or register to comment.")
        return redirect(url_for("home"))
    form = AddTask()
    if form.validate_on_submit():
        new_task = Tasks(
            task=form.task.data,
            status="NOT_COMPLETE",
            list_id=list_id,
            user_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("show_tasks", list_id=list_id))
    return render_template("add_task.html", form=form, current_user=current_user)


@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):
    task_to_delete = Tasks.query.get(task_id)
    list_id = task_to_delete.list_id
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for('show_tasks', list_id=list_id))


@app.route("/complete/<int:task_id>", methods=["GET", "POST"])
def task_complete(task_id):
    task = Tasks.query.get(task_id)
    if task.status == "NOT_COMPLETE":
        task.status = "COMPLETE"
    else:
        task.status = "NOT_COMPLETE"
    db.session.commit()
    return redirect(url_for('show_tasks', list_id=task.list_id))


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
