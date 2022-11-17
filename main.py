from flask import Flask, request, render_template, redirect, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from data import db_session
from data.user import User

import datetime

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "Пожалуйста, войдите, что бы получить доступ к этой странице."


@login_manager.user_loader
def load_user(user_id: int):
    db_sess = db_session.create_session()
    return db_sess.query(User).filter(User.id == user_id).first()


def password_is_correct(password: str):
    if password.islower() or password.isupper() or len(password) < 8:
        return False
    for i in password.lower():
        if i not in "abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789!@$#_":
            return False
    digits = ""
    special = ""
    for i in "0123456789":
        if i in password:
            digits += i
    for i in "!@$#":
        if i in password:
            special += i
    if not special or not digits:
        return False
    return True


app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'static/media/from_users'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024


@app.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect("/user/" + current_user.login)
    return render_template("index.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        if request.form["password"] == request.form["password_sec"] and password_is_correct(request.form["password"]):
            db_sess = db_session.create_session()
            existing_user = db_sess.query(User).filter(User.login == request.form["login"]).first()
            if existing_user:
                flash("Ошибка регистрации: кто-то уже есть с таким логином", "danger")
                return redirect("/signup")
            existing_user = db_sess.query(User).filter(User.email == request.form["email"]).first()
            if existing_user:
                flash("Ошибка регистрации: кто-то уже есть с такой почтой", "danger")
                return redirect("/signup")
            user = User()
            user.name = request.form["name"]
            user.surname = request.form["surname"]
            user.email = request.form["email"]
            user.login = request.form["login"]
            user.hashed_password = generate_password_hash(request.form["password"])
            db_sess.add(user)
            db_sess.commit()
            login_user(user)
            user.last_auth = datetime.datetime.now()
            flash("Регистрация прошла успешно!", "success")
            return redirect("/user/" + user.login)
        elif password_is_correct(request.form["password"]):
            flash("Ошибка регистрации: пароль не повторён", "danger")
            return redirect("/signup")
        else:
            flash("Ошибка регистрации: пароль не удовлетворяет требованию", "danger")
            return redirect("/signup")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect("/user/" + current_user.login)
        return render_template("login.html")
    elif request.method == "POST":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == request.form["login"]).first()
        if user and check_password_hash(user.hashed_password, request.form["password"]):
            login_user(user)
            user.last_auth = datetime.datetime.now()
            flash("Успешный вход", "success")
            return redirect("/user/" + user.login)
        else:
            flash("Ошибка входа: неверный пароль", "danger")
            return redirect("/login")


@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/user/<username>", methods=["POST", "GET"])
def user_page(username):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == username).first()
    if user:
        if request.method == "GET":
            return render_template("user.html", user=user, current_user=current_user)
        elif request.method == "POST":
            if current_user == user and "about_button" in request.form:
                user.about = request.form["about_input"]
                db_sess.commit()
                flash("Описание успешно обновлено", "success")
                return redirect("/user/" + username)
    else:
        abort(404)


@app.errorhandler(401)
def e401():
    flash("Данную страницу можно смотреть только авторизованным пользователям", "warning")
    return redirect("/login")


if __name__ == "__main__":
    db_session.global_init("db/social_network.db")
    app.run(host="0.0.0.0", port=8080)