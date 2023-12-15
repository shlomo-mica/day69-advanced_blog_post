from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from functools import wraps

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, ConnentForm

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)

# TODO: Configure Flask-Login

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()


# CONFIGURE TABLES
class BlogPost(db.Model, UserMixin):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# TODO: Create a User table for all your registered users.
class Users(db.Model, UserMixin):
    __tablename__ = "register"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(100), unique=True)
    user_password = db.Column(db.String(100))
    user_name = db.Column(db.String(100))


db.init_app(app)
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(id1):
    return Users.query.get(int(id1))


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    test1 = 'new register hi'
    form = RegisterForm()
    if request.method == 'POST':
        user = Users(user_name=form.name.data, user_mail=form.email.data,
                     user_password=generate_password_hash(form.password.data, "pbkdf2", salt_length=2))

        db.session.add(user)
        db.session.commit()
        a = 'new_one'
        flash("gggg")
        return redirect(url_for('login', test=a))
        # name = request.form['name']
        # email = request.form["email"]
        # password = request.form['password']

    return render_template("register.html", form=form, test=test1)


def find_admin_by_email(form_email, form_password):
    try:
        find_admin = Users.query.filter_by(user_mail=form_email, id=12, user_password=form_password).first()
        mail_login = Users.query.filter_by(user_mail=form_email).first()

        if check_password_hash(mail_login.user_password, form_password) and find_admin:
            print("admin approved")
            return True
    except:
        return False


# TODO: Retrieve a user from the database based on their email.
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':

        admin_login = find_admin_by_email(request.form.get('email'), request.form.get('password'))

        if admin_login:
            print("Admin entered")
            flash("Hello Admin")
            # return redirect(f'/get_all_posts/{a}')
            return redirect(url_for('get_all_posts'))

        else:
            print("regular user enter")
            all_record = Users.query.all()  # CALL ALL RECORDS IN DATABASE
            mail_login = Users.query.filter_by(user_mail=request.form.get('email')).first()
            print("stage1")
            if mail_login:

                print("stage 2")

                if check_password_hash(mail_login.user_password, request.form.get('password')):

                    print("stage 3")
                    login_user(mail_login, remember=True)
                    flash("Password match")

                    return redirect(url_for("get_all_posts"))

                else:
                    flash("Email or Password dont match")

    return render_template("login.html", form=form)


# # duser = db.one_or_404(db.select(Users).filter_by(user_name='didi'))
# exist = db.session.query(Users.user_mail).filter_by(user_mail=request.form.get('email'))
# user_login = Users.query.filter_by(user_mail=request.form.get('email')).first()
# admin_only = db.session(db.select(Users.user_mail).where(Users.id == 1)).first()

@app.route('/logout')
def logout():
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
