from flask import Flask, request, render_template, redirect, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from data import db_session
from data.user import User

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "Пожалуйста, войдите, что бы получить доступ к этой странице."


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).filter(User.id == user_id).first()


app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'static/media/from_users'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        if request.form["password"] == request.form["password_sec"]:
            db_sess = db_session.create_session()
            user = User()
            user.name = request.form["name"]
            user.surname = request.form["surname"]
            user.email = request.form["email"]
            user.login = request.form["login"]
            user.hashed_password = generate_password_hash(request.form["password"])
            db_sess.add(user)
            db_sess.commit()
            login_user(user)
            flash('Успешная регистрация', "success")
            return redirect(f"/user/{user.login}")
        else:
            return "пароль введён некорректно"


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == request.form["login"]).first()
        if check_password_hash(user.hashed_password, request.form["password"]):
            login_user(user)
            flash('Успешный вход', "success")
            return redirect(f"/user/{user.login}")
        else:
            return "пароль введён некорректно"


@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/user/<username>", methods=["GET"])
def user_page(username):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == username).first()
    if user:
        return render_template("user.html", login=username, is_authenticated=current_user.is_authenticated)
    else:
        abort(404)


if __name__ == "__main__":
    db_session.global_init("db/social_network.db")
    app.run(host="0.0.0.0", port=8080)