from flask import Flask, request, render_template, redirect, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from data import db_session
from data.user import User
from data.post import Post

import datetime

import os

is_xp = False  # Для корректной работы на моём нетбуке с Windows XP :)

AVATAR_TYPES = ["png", "jpg", "jpeg", "gif"]
POST_MEDIA_PIC_TYPES = ["png", "jpg", "jpeg", "gif"]
POST_MEDIA_VID_TYPES = ["webm", "mp4"]
POST_MEDIA_AUD_TYPES = ["mp3", "wav"]
POST_MEDIA_TYPES = POST_MEDIA_VID_TYPES + POST_MEDIA_PIC_TYPES + POST_MEDIA_AUD_TYPES
MAX_MEDIA_COUNT = 8


def make_accept_for_html(mime: str):
    # For input tag in HTML
    if mime in POST_MEDIA_PIC_TYPES:
        return "image/" + mime
    elif mime in POST_MEDIA_VID_TYPES:
        return "video/" + mime
    elif mime in POST_MEDIA_AUD_TYPES:
        return "audio/" + mime


def make_readble_time(t: datetime.datetime):
    new_t = str(t).split()
    new_t[0] = new_t[0].split("-")[::-1]
    new_t[0] = ".".join(new_t[0])
    new_t[1] = new_t[1].split(".")[0]
    new_t = " ".join(new_t)
    return new_t


accept_avatars = ",".join([make_accept_for_html(x) for x in AVATAR_TYPES])
accept_post_media = ",".join([make_accept_for_html(x) for x in POST_MEDIA_TYPES])


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "Данную страницу можно смотреть только авторизованным пользователям"


@login_manager.user_loader
def load_user(user_id: int):
    db_sess = db_session.create_session()
    return db_sess.query(User).filter(User.id == user_id).first()


def login_is_correct(login_s: str):
    if not login_s.replace(" ", "") or len(login_s) > 32:
        return False
    for i in login_s.lower():
        if i not in "abcdefghijklmnopqrstuvwxyz0123456789_":
            return False
    return True


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


def update_user_auth_time():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(current_user.id == User.id).first()
        user.last_auth = datetime.datetime.now()
        db_sess.commit()


def allowed_type(filename, types):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in types


app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'static/media/from_users'
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024


@app.route("/", methods=["GET"])
def index():
    update_user_auth_time()
    if current_user.is_authenticated:
        return redirect("/user/" + current_user.login)
    return render_template("index.html")


@app.route("/user/<username>", methods=["POST", "GET"])
def user_page(username):
    update_user_auth_time()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == username).first()
    if user:
        user_time = make_readble_time(user.last_auth)
        posts = db_sess.query(Post).filter(user.id == Post.poster_id)
        if request.method == "GET":
            post_time = {}
            post_media = {}
            post_media_type = {}
            post_media_count = {}
            for post in posts:
                post_time[post.id] = make_readble_time(post.creation_date)
                if post.media:
                    post_media[post.id] = post.media.split(", ")
                    post_media_type[post.id] = post.media_type.split(", ")
                    post_media_count[post.id] = len(post.media.split(", "))
            return render_template("user.html", user=user, current_user=current_user, posts=posts,
                                   posts_c=posts.count(), media_pics=POST_MEDIA_PIC_TYPES,
                                   media_vid=POST_MEDIA_VID_TYPES, media_aud=POST_MEDIA_AUD_TYPES,
                                   accept_files=accept_post_media, post_time=post_time, user_time=user_time,
                                   max_size=app.config['MAX_CONTENT_LENGTH'] // 1024 // 1024,
                                   max_count=MAX_MEDIA_COUNT, post_media=post_media, post_media_type=post_media_type,
                                   post_media_count=post_media_count)
        elif request.method == "POST":
            if current_user.is_authenticated:
                if "like_button" in request.form:
                    post = db_sess.query(Post).filter(Post.id == request.form["like_button"]).first()
                    if post:
                        who_liked = post.who_liked.split(", ")
                        if str(current_user.id) in who_liked:
                            who_liked.remove(str(current_user.id))
                            post.likes -= 1
                            msg = "Лайк убран"
                        else:
                            who_liked.append(str(current_user.id))
                            post.likes += 1
                            msg = "Лайк поставлен"
                        post.who_liked = ", ".join(who_liked)
                        db_sess.commit()
                        flash(msg, "success")
                    return redirect("/user/" + username)
                if current_user == user:
                    if "about_button" in request.form:
                        user.about = request.form["about_input"]
                        db_sess.commit()
                        flash("Описание успешно обновлено", "success")
                    elif "post_button" in request.form:
                        post = Post()
                        new_id = db_sess.query(Post).count() + 1
                        files = request.files.getlist("files[]")
                        too_many_files = False
                        if files:
                            media = []
                            media_type = []
                            f_count = 0
                            for file in files:
                                if allowed_type(file.filename, POST_MEDIA_TYPES) and f_count < MAX_MEDIA_COUNT:
                                    filename = "post" + str(current_user.id) + "_" + str(new_id) + "_" + \
                                               str(f_count) + "." + file.filename.rsplit('.', 1)[1].lower()
                                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                                    media.append(filename)
                                    media_type.append(filename.rsplit('.', 1)[1].lower())
                                    f_count += 1
                                elif f_count >= MAX_MEDIA_COUNT:
                                    too_many_files = True
                                    break
                            if media:
                                post.media = ", ".join(media)
                            if media_type:
                                post.media_type = ", ".join(media_type)
                        post.poster_id = current_user.id
                        post.text = request.form["text"]
                        db_sess.add(post)
                        db_sess.commit()
                        if too_many_files:
                            flash("Пост отправлен, но был превышен лимит файлов на один пост, поэтому"
                                  " часть из них была отброшена", "warning")
                        else:
                            flash("Пост успешно отправлен", "success")
                else:
                    flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
                return redirect("/user/" + username)
    else:
        abort(404)


@app.route("/settings", methods=["POST", "GET"])
@login_required
def settings():
    update_user_auth_time()
    if request.method == "GET":
        return render_template("settings.html", current_user=current_user, accept_avatars=accept_avatars)
    elif request.method == "POST":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if "clear_button" in request.form and user.avatar != None:
            if os.path.isfile("static/media/from_users/avatars/" + user.avatar):
                os.remove("static/media/from_users/avatars/" + user.avatar)
            user.avatar = None
            db_sess.commit()
        elif "set_button" in request.form:
            if request.form.get("name"):
                user.name = request.form["name"]
            if request.form.get("surname"):
                user.surname = request.form["surname"]
            if request.form.get("login"):
                existing_user = db_sess.query(User).filter(User.login == request.form["login"]).first()
                if existing_user:
                    flash("Ошибка обновления: кто-то уже есть с таким логином", "danger")
                    return redirect("/user/" + current_user.login)
            if request.form.get("email"):
                existing_user = db_sess.query(User).filter(User.email == request.form["email"]).first()
                if existing_user:
                    flash("Ошибка обновления: кто-то уже есть с такой почтой", "danger")
                    return redirect("/user/" + current_user.login)
            if request.form.get("only_friends"):
                user.posts_only_for_friends = True
            else:
                user.posts_only_for_friends = False
            if request.form.get("messages_only_friends"):
                user.talk_only_with_friends = True
            else:
                user.talk_only_with_friends = False
            file = request.files["file"]
            if file and allowed_type(file.filename, AVATAR_TYPES):
                if user.avatar != None:
                    if os.path.isfile("static/media/from_users/avatars/" + user.avatar):
                        os.remove("static/media/from_users/avatars/" + user.avatar)
                filename = "avatar" + str(user.id) + "." + file.filename.rsplit('.', 1)[1].lower()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/avatars", filename))
                user.avatar = filename
            db_sess.commit()
        flash("Настройки обновлены", "success")
        return redirect("/user/" + current_user.login)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    update_user_auth_time()
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect("/user/" + current_user.login)
        return render_template("signup.html")
    elif request.method == "POST":
        if not request.form["name"].replace(" ", "") or len(request.form["name"]) > 32:
            flash("Ошибка регистрации: имя не удовлетворяет требованию", "danger")
            return redirect("/signup")
        elif not request.form["surname"].replace(" ", "") or len(request.form["surname"]) > 32:
            flash("Ошибка регистрации: фамилия не удовлетворяет требованию", "danger")
            return redirect("/signup")
        elif not request.form["login"].replace(" ", "") or not login_is_correct(request.form["login"]):
            flash("Ошибка регистрации: логин не удовлетворяет требованию", "danger")
            return redirect("/signup")
        elif len(request.form["email"]) > 64:
            flash("Ошибка регистрации: электронная почта не удовлетворяет требованию", "danger")
            return redirect("/signup")
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
    update_user_auth_time()
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect("/user/" + current_user.login)
        return render_template("login.html")
    elif request.method == "POST":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.login == request.form["login"])
                                          | (User.email == request.form["login"])).first()
        if user and check_password_hash(user.hashed_password, request.form["password"]):
            login_user(user)
            user.last_auth = datetime.datetime.now()
            flash("Успешный вход", "success")
            return redirect("/user/" + user.login)
        elif not user:
            flash("Ошибка входа: неверный логин", "danger")
            return redirect("/login")
        elif not check_password_hash(user.hashed_password, request.form["password"]):
            flash("Ошибка входа: неверный пароль", "danger")
            return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    update_user_auth_time()
    logout_user()
    if request.args.get("from") != None:
        return redirect(request.args.get("from"))
    return redirect("/")


@app.errorhandler(401)
def e401(code):
    update_user_auth_time()
    print(code)
    flash("[Ошибка 401] " + login_manager.login_message, "warning")
    return redirect("/login")


@app.errorhandler(403)
def e403(code):
    update_user_auth_time()
    print(code)
    flash("[Ошибка 403] Данную страницу можно смотреть только администраторам", "warning")
    return redirect("/login")


if __name__ == "__main__":
    db_session.global_init("db/social_network.db")
    if is_xp:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host = s.getsockname()[0]
        s.close()
        app.run(host=host, port=8080)
    else:
        app.run(host="0.0.0.0", port=8080)
