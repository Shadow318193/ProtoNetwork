import random

from flask import Flask, request, render_template, redirect, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from data import db_session
from data.user import User
from data.post import Post
from data.news import News
from data.public import Public
from data.messages import Message

import datetime

import os

from time import time

from platform import release

PYTHONANYWHERE = False
is_xp = True if release() == "XP" and not PYTHONANYWHERE else False

AVATAR_TYPES = ["png", "jpg", "jpeg", "gif"]
POST_MEDIA_PIC_TYPES = ["png", "jpg", "jpeg", "gif"]
POST_MEDIA_VID_TYPES = ["webm", "mp4"]
POST_MEDIA_AUD_TYPES = ["mp3", "wav"]
POST_MEDIA_TYPES = POST_MEDIA_VID_TYPES + POST_MEDIA_PIC_TYPES + POST_MEDIA_AUD_TYPES
MAX_MEDIA_COUNT = 8 if not PYTHONANYWHERE else 5
POSTS_IN_PAGE_MAX = 10

PICS_404 = ["masha.png", "johnny.gif"]
PICS_500 = ["masyanya.png", "vovka.png", "baby.jpg", "fedor.png"]


def make_accept_for_html(mime: str):
    # For input tag in HTML
    if mime in POST_MEDIA_PIC_TYPES:
        return "image/" + mime
    elif mime in POST_MEDIA_VID_TYPES:
        return "video/" + mime
    elif mime in POST_MEDIA_AUD_TYPES:
        return "audio/" + mime


def make_readble_time(t: datetime.datetime):
    # Time format: dd.MM.yyyy hh:mm
    new_t = str(t).split()
    new_t[0] = new_t[0].split("-")[::-1]
    new_t[0] = ".".join(new_t[0])
    new_t[1] = new_t[1].split(".")[0]
    new_t = " ".join(new_t)
    return new_t


def make_text_news(text: str):
    if len(text) > 100:
        return text[:100] + "..."
    else:
        return text


accept_avatars = ",".join([make_accept_for_html(x) for x in AVATAR_TYPES])
accept_post_media = ",".join([make_accept_for_html(x) for x in POST_MEDIA_TYPES])


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "Cмотреть данную страницу/делать данное действие можно " \
                              "только авторизованным пользователям"


@login_manager.user_loader
def load_user(user_id: int):
    db_sess = db_session.create_session()
    return db_sess.query(User).filter(User.id == user_id).first()


def name_is_correct(name_s: str):
    if not name_s:
        return False
    if not name_s.split() or len(name_s) > 32:
        return False
    for i in name_s.lower():
        if i not in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя":
            return False
    return True


def login_is_correct(login_s: str):
    if not login_s:
        return False
    if not login_s.split() or len(login_s) > 32:
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
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024 if not PYTHONANYWHERE else 16 * 1024 * 1024


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
        if not request.args.get("page"):
            return redirect("/user/" + username + "?page=1")
        else:
            try:
                page = int(request.args["page"])
                if page < 1:
                    return redirect("/user/" + username + "?page=1")
            except ValueError:
                return redirect("/user/" + username + "?page=1")
        user_creation_time = make_readble_time(user.creation_date)
        user_time = make_readble_time(user.last_auth)
        if current_user.is_authenticated and user != current_user:
            the_user_is_friend = str(current_user.id) in user.friends.split(", ")
            if str(user.id) in current_user.friends_req.split(", "):
                user_req = user.id
            elif str(current_user.id) in user.friends_req.split(", "):
                user_req = current_user.id
            else:
                user_req = 0
            user_friend = str(user.id) in current_user.friends.split(", ")
        else:
            user_req = None
            user_friend = None
            the_user_is_friend = None
        posts = db_sess.query(Post).filter(user.id == Post.poster_id, Post.parent_post == None, Post.public_id == None)
        posts_c = posts.count()
        if posts_c:
            max_page_of_user = posts_c // POSTS_IN_PAGE_MAX
            if posts_c % POSTS_IN_PAGE_MAX:
                max_page_of_user += 1
        else:
            max_page_of_user = 1
        if page > max_page_of_user and page != 1:
            return redirect("/user/" + username + "?page=" + str(max_page_of_user))
        if request.method == "GET":
            last_n = db_sess.query(News).get(db_sess.query(News).count())
            if last_n:
                last_n_time = make_readble_time(last_n.creation_date)
            else:
                last_n_time = None
            post_time = {}
            post_media = {}
            post_media_type = {}
            post_media_count = {}
            post_likers = {}
            for post in posts:
                post_time[post.id] = make_readble_time(post.creation_date)
                if post.media:
                    post_media[post.id] = post.media.split(", ")
                    post_media_type[post.id] = post.media_type.split(", ")
                    post_media_count[post.id] = len(post.media.split(", "))
                post_likers[post.id] = post.who_liked.split(", ")
                if "" in post_likers[post.id]:
                    post_likers[post.id].remove("")
            comments = {}
            comments_posters = {}
            comments_time = {}
            comments_likers = {}
            for p in posts:
                comments[p.id] = db_sess.query(Post).filter(Post.parent_post == p.id)
                for comm in comments[p.id]:
                    comments_posters[comm.id] = db_sess.query(User).filter(comm.poster_id == User.id).first()
                    comments_time[comm.id] = make_readble_time(comm.creation_date)
                    comments_likers[comm.id] = comm.who_liked.split(", ")
                    if "" in comments_likers[comm.id]:
                        comments_likers[comm.id].remove("")
            return render_template("user.html", user=user, current_user=current_user, posts=posts, posts_c=posts_c,
                                   media_pics=POST_MEDIA_PIC_TYPES, post_likers=post_likers,
                                   media_vid=POST_MEDIA_VID_TYPES, media_aud=POST_MEDIA_AUD_TYPES,
                                   accept_files=accept_post_media, post_time=post_time, user_time=user_time,
                                   max_size=app.config['MAX_CONTENT_LENGTH'] // 1024 // 1024,
                                   max_count=MAX_MEDIA_COUNT, post_media=post_media, post_media_type=post_media_type,
                                   post_media_count=post_media_count, user_req=user_req, user_friend=user_friend,
                                   the_user_is_friend=the_user_is_friend, last_n=last_n, last_n_time=last_n_time,
                                   last_n_text=make_text_news(last_n.text) if last_n else None, page=page,
                                   page_max=POSTS_IN_PAGE_MAX, max_page_of_user=max_page_of_user,
                                   comments=comments, comments_posters=comments_posters, comments_time=comments_time,
                                   comments_likers=comments_likers, user_creation_time=user_creation_time)
        elif request.method == "POST":
            if "to_the_beginning_button" in request.form:
                return redirect("/user/" + username + "?page=" + str(request.form["to_the_beginning_button"]))
            elif "to_the_end_button" in request.form:
                return redirect("/user/" + username + "?page=" + str(request.form["to_the_end_button"]))
            elif "to_the_previous_button" in request.form:
                return redirect("/user/" + username + "?page=" + str(request.form["to_the_previous_button"]))
            elif "to_the_next_button" in request.form:
                return redirect("/user/" + username + "?page=" + str(request.form["to_the_next_button"]))
            if current_user.is_authenticated:
                if "like_button" in request.form and (current_user == user or not user.posts_only_for_friends):
                    post = db_sess.query(Post).filter(Post.id == request.form["like_button"]).first()
                    if post:
                        who_liked = post.who_liked.split(", ")
                        if "" in who_liked:
                            who_liked.remove("")
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
                    return redirect("/user/" + username + "?page=" + str(page))
                if current_user == user:
                    if "about_button" in request.form and not current_user.is_banned:
                        user.about = request.form["about_input"]
                        db_sess.commit()
                        flash("Описание успешно обновлено", "success")
                    elif "post_button" in request.form and not current_user.is_banned:
                        post = Post()
                        files = request.files.getlist("files[]")
                        too_many_files = False
                        if files:
                            media = []
                            media_type = []
                            f_count = 0
                            for file in files:
                                if allowed_type(file.filename, POST_MEDIA_TYPES) and f_count < MAX_MEDIA_COUNT:
                                    filename = str(time()).replace(".", "_") + "_" + str(f_count) + "." + \
                                               file.filename.rsplit('.', 1)[1].lower()
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
                        return redirect("/user/" + username + "?page=1")
                    elif "comment_button" in request.form and not current_user.is_banned:
                        if request.form.get("comment_text").replace(" ", ""):
                            comment = Post()
                            comment.poster_id = current_user.id
                            comment.parent_post = request.form["comment_button"]
                            comment.text = request.form["comment_text"]
                            db_sess.add(comment)
                            db_sess.commit()
                            flash("Комментарий успешно отправлен", "success")
                        else:
                            flash("Сначала нужно что-нибудь написать", "danger")
                    elif "delete_post_button" in request.form and not current_user.is_banned:
                        post = db_sess.query(Post).filter(Post.id == request.form["delete_post_button"]).first()
                        if post.media:
                            files_to_delete = post.media.split(", ")
                            for f in files_to_delete:
                                if os.path.isfile("static/media/from_users/" + f):
                                    os.remove("static/media/from_users/" + f)
                        db_sess.delete(post)
                        db_sess.commit()
                        flash("Пост успешно удалён", "success")
                    elif current_user.is_banned:
                        flash("Ты был забанен, поэтому отправлять с этого аккаунта больше ничего нельзя, "
                              "только смотреть. Причина бана: " + current_user.ban_reason, "danger")
                else:
                    if "ban_user_button" in request.form and current_user.is_admin and not user.is_banned:
                        if request.form.get("reason_text") and not user.is_admin:
                            user.ban_reason = request.form["reason_text"]
                            user.is_banned = True
                            db_sess.commit()
                            flash("Пользователь успешно забанен", "success")
                        elif user.is_admin:
                            flash("Нельзя блокировать администраторов", "danger")
                        else:
                            flash("Необходимо указать причину бана", "danger")
                    elif "unban_user_button" in request.form and current_user.is_admin and user.is_banned and not user.is_admin:
                        user.ban_reason = None
                        user.is_banned = False
                        db_sess.commit()
                        flash("Пользователь успешно разбанен", "success")
                    elif "delete_post_button" in request.form and not current_user.is_banned:
                        post = db_sess.query(Post).filter(Post.id == request.form["delete_post_button"]).first()
                        if post.poster_id == current_user.id or current_user.is_admin:
                            if post.media:
                                files_to_delete = post.media.split(", ")
                                for f in files_to_delete:
                                    if os.path.isfile("static/media/from_users/" + f):
                                        os.remove("static/media/from_users/" + f)
                            db_sess.delete(post)
                            db_sess.commit()
                            flash("Пост успешно удалён", "success")
                        else:
                            flash("Нельзя удалить этот пост", "danger")
                    elif "unmake_user_news_pub_button" in request.form and current_user.is_news_publisher and not user.is_banned:
                        user.is_news_publisher = False
                        db_sess.commit()
                        flash("У пользователя отобрана возможность публиковать новости", "success")
                    elif "make_user_news_pub_button" in request.form and not current_user.is_news_publisher and not user.is_banned:
                        user.is_news_publisher = True
                        db_sess.commit()
                        flash("Пользователю дана возможность публиковать новости", "success")
                    elif "comment_button" in request.form and not user.posts_only_for_friends and \
                            not current_user.is_banned and not user.is_banned:
                        if request.form.get("comment_text").replace(" ", ""):
                            comment = Post()
                            comment.poster_id = current_user.id
                            comment.parent_post = request.form["comment_button"]
                            comment.text = request.form["comment_text"]
                            db_sess.add(comment)
                            db_sess.commit()
                            flash("Комментарий успешно отправлен", "success")
                        else:
                            flash("Сначала нужно что-нибудь написать", "danger")
                    elif "friend_request_button" in request.form and not user_req and not user_friend:
                        user_friends_req = user.friends_req.split(", ")
                        if "" in user_friends_req:
                            user_friends_req.remove("")
                        user_friends_req.append(str(current_user.id))
                        user.friends_req = ", ".join(user_friends_req)
                        db_sess.commit()
                        flash("Заявка отправлена", "success")
                    elif "make_friends_button" in request.form and user_req and not user_friend:
                        user_friends = user.friends.split(", ")
                        if "" in user_friends:
                            user_friends.remove("")
                        the_user = db_sess.query(User).filter(User.id == current_user.id).first()
                        current_user_friends = the_user.friends.split(", ")
                        if "" in current_user_friends:
                            current_user_friends.remove("")
                        current_user_friends_req = the_user.friends_req.split(", ")
                        if "" in current_user_friends_req:
                            current_user_friends_req.remove("")
                        current_user_friends_req.remove(str(user.id))
                        the_user.friends_req = ", ".join(current_user_friends_req)
                        user_friends.append(str(current_user.id))
                        current_user_friends.append(str(user.id))
                        the_user.friends = ", ".join(current_user_friends)
                        user.friends = ", ".join(user_friends)
                        user.friends_num += 1
                        the_user.friends_num += 1
                        db_sess.commit()
                        flash("Теперь вы друзья", "success")
                    elif "no_friends_now_button" in request.form and not user_req and user_friend:
                        user_friends = user.friends.split(", ")
                        the_user = db_sess.query(User).filter(User.id == current_user.id).first()
                        current_user_friends = the_user.friends.split(", ")
                        user_friends.remove(str(current_user.id))
                        current_user_friends.remove(str(user.id))
                        the_user.friends = ", ".join(current_user_friends)
                        user.friends = ", ".join(user_friends)
                        user.friends_num -= 1
                        the_user.friends_num -= 1
                        db_sess.commit()
                        flash("Вы больше не друзья", "success")
                    elif "friend_request_button" in request.form and user_req:
                        flash("Этот пользователь уже прислал вам заявку", "danger")
                    elif "no_friends_now_button" in request.form and not user_friend:
                        flash("Этого пользователя нет в друзьях", "danger")
                    else:
                        flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
                return redirect("/user/" + username + "?page=" + str(page))
            else:
                abort(401)
    else:
        abort(404)


@app.route("/settings", methods=["POST", "GET"])
@login_required
def settings():
    update_user_auth_time()
    if request.method == "GET":
        if current_user.is_banned:
            flash("Нельзя настраивать забаненный аккаунт", "danger")
            return redirect("/user/" + current_user.login)
        return render_template("settings.html", current_user=current_user, accept_avatars=accept_avatars)
    elif request.method == "POST":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if not current_user.is_banned:
            all_is_ok = True
            error_message = "Настройки обновлены частично, случились проблемы с:"
            if "clear_button" in request.form and user.avatar:
                if os.path.isfile("static/media/from_users/avatars/" + user.avatar):
                    os.remove("static/media/from_users/avatars/" + user.avatar)
                user.avatar = None
                db_sess.commit()
            elif "set_button" in request.form:
                if name_is_correct(request.form.get("name")):
                    user.name = request.form["name"]
                elif request.form.get("name") != "" and request.form.get("name") != None:
                    error_message += "\nИменем"
                    all_is_ok = False
                if name_is_correct(request.form.get("surname")):
                    user.surname = request.form["surname"]
                elif request.form.get("surname") != "" and request.form.get("surname") != None:
                    error_message += "\nФамилией"
                    all_is_ok = False
                if login_is_correct(request.form.get("login")):
                    existing_user = db_sess.query(User).filter(User.login == request.form["login"]).first()
                    if existing_user:
                        error_message += "\nЛогином (он уже есть на сайте)"
                        all_is_ok = False
                    else:
                        user.login = request.form["login"]
                elif request.form.get("login") != "" and request.form.get("login") != None:
                    error_message += "\nЛогином"
                if request.form.get("email"):
                    existing_user = db_sess.query(User).filter(User.email == request.form["email"]).first()
                    if existing_user:
                        error_message += "\nПочтой (она уже есть на сайте)"
                        all_is_ok = False
                    else:
                        user.email = request.form["email"]
                elif request.form.get("email") != "" and request.form.get("email") != None:
                    error_message += "\nПочтой"
                if request.form.get("old_password") and request.form.get("new_password") and \
                        request.form.get("confirm_new_password"):
                    if request.form["new_password"] == request.form["confirm_new_password"] and \
                            check_password_hash(user.hashed_password, request.form["old_password"]) and \
                            password_is_correct(request.form["new_password"]):
                        user.hashed_password = generate_password_hash(request.form["new_password"])
                    else:
                        all_is_ok = False
                        error_message += "\nПаролем"
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
                elif file and not allowed_type(file.filename, AVATAR_TYPES):
                    error_message += "\nАватаркой"
                    all_is_ok = False
                db_sess.commit()
            if all_is_ok:
                flash("Настройки обновлены", "success")
            else:
                flash(error_message, "warning")
        else:
            flash("Нельзя настраивать забаненный аккаунт", "danger")
        return redirect("/user/" + user.login)


@app.route("/friends", methods=["POST", "GET"])
@login_required
def friends():
    update_user_auth_time()
    db_sess = db_session.create_session()
    requested_users = current_user.friends_req.split(", ")
    friends_users = current_user.friends.split(", ")
    if "" in requested_users:
        requested_users.remove("")
    if "" in friends_users:
        friends_users.remove("")
    requested_users_real = db_sess.query(User).filter(User.id != current_user.id)
    friends_users_real = db_sess.query(User).filter(User.id != current_user.id)
    if request.method == "GET":
        last_n = db_sess.query(News).get(db_sess.query(News).count())
        if last_n:
            last_n_time = make_readble_time(last_n.creation_date)
        else:
            last_n_time = None
        return render_template("friends.html", users_req=requested_users_real, users_friends=friends_users_real,
                               current_user=current_user, users_req_c=len(requested_users),
                               users_friends_c=len(friends_users), users_req_l=requested_users,
                               users_friends_l=friends_users, last_n=last_n, last_n_time=last_n_time,
                               last_n_text=make_text_news(last_n.text) if last_n else None)
    elif request.method == "POST":
        if "make_friends_button" in request.form or "not_friends_button" in request.form:
            if "make_friends_button" in request.form:
                if request.form["make_friends_button"] == current_user.id:
                    flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
                    return redirect("/friends")
                the_user = db_sess.query(User).filter(User.id == request.form["make_friends_button"]).first()
                if not the_user or str(the_user.id) not in requested_users:
                    flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
                    return redirect("/friends")
            elif "not_friends_button" in request.form:
                if request.form["not_friends_button"] == current_user.id:
                    flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
                    return redirect("/friends")
                the_user = db_sess.query(User).filter(User.id == request.form["no_friends_button"]).first()
                if not the_user or str(the_user.id) not in friends_users:
                    flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
                    return redirect("/friends")
            my_user = db_sess.query(User).filter(User.id == current_user.id).first()
            if "make_friends_button" in request.form:
                the_user_friends = the_user.friends.split(", ")
                requested_users.remove(str(the_user.id))
                my_user.friends_req = ", ".join(requested_users)
                the_user_friends.append(str(current_user.id))
                friends_users.append(str(the_user.id))
                the_user.friends = ", ".join(the_user_friends)
                my_user.friends = ", ".join(friends_users)
                my_user.friends_num += 1
                the_user.friends_num += 1
                db_sess.commit()
                flash("Теперь вы друзья", "success")
            elif "no_friends_button" in request.form:
                requested_users.remove(str(the_user.id))
                my_user.friends_req = ", ".join(requested_users)
                db_sess.commit()
                flash("Отказано в дружбе", "success")
        else:
            flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
        return redirect("/friends")


@app.route("/signup", methods=["POST", "GET"])
def signup():
    update_user_auth_time()
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect("/user/" + current_user.login)
        return render_template("signup.html")
    elif request.method == "POST":
        if not name_is_correct(request.form["name"]):
            flash("Ошибка регистрации: имя не удовлетворяет требованию", "danger")
            return redirect("/signup")
        elif not name_is_correct(request.form["surname"]):
            flash("Ошибка регистрации: фамилия не удовлетворяет требованию", "danger")
            return redirect("/signup")
        elif not login_is_correct(request.form["login"]):
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
            if request.args.get("from"):
                return redirect(request.args.get("from"))
            return redirect("/user/" + user.login)
        elif not user:
            flash("Ошибка входа: неверный логин", "danger")
            return redirect("/login")
        elif not check_password_hash(user.hashed_password, request.form["password"]):
            flash("Ошибка входа: неверный пароль", "danger")
            return redirect("/login")


@app.route("/search", methods=["POST", "GET"])
def search():
    update_user_auth_time()
    if request.method == "GET":
        db_sess = db_session.create_session()
        last_n = db_sess.query(News).get(db_sess.query(News).count())
        if last_n:
            last_n_time = make_readble_time(last_n.creation_date)
        else:
            last_n_time = None
        text_to_search = request.args.get("req")
        if current_user.is_authenticated:
            users = db_sess.query(User).filter(User.id != current_user.id)
        else:
            users = db_sess.query(User)
        publics = db_sess.query(Public)
        needed_users = []
        needed_publics = []
        if text_to_search:
            text_to_search = [x.lower() for x in text_to_search.split("+")]
            for user in users:
                for t in text_to_search:
                    if user.patronymic:
                        if t in user.name.lower() or t in user.surname.lower() or t in user.login.lower() or \
                                t in user.patronymic.lower():
                            needed_users.append(user)
                    else:
                        if t in user.name.lower() or t in user.surname.lower() or t in user.login.lower():
                            needed_users.append(user)
            for public in publics:
                for t in text_to_search:
                    if t in public.name.lower():
                        needed_publics.append(public)
            users_c = len(needed_users)
            publics_c = len(needed_publics)
        else:
            users_c = users.count()
            publics_c = publics.count()
        return render_template("search.html", current_user=current_user, text_to_search=text_to_search,
                               users=needed_users if text_to_search else users, users_c=users_c,
                               last_n=last_n, last_n_time=last_n_time, publics_c=publics_c,
                               last_n_text=make_text_news(last_n.text) if last_n else None,
                               publics=needed_publics if text_to_search else publics)
    elif request.method == "POST":
        return redirect("/search?req=" + request.form.get("text_to_search").replace(" ", "+"))


@app.route("/news", methods=["POST", "GET"])
def news_page():
    update_user_auth_time()
    db_sess = db_session.create_session()
    if request.method == "GET":
        news = db_sess.query(News)
        n_time = {}
        n_media = {}
        n_media_type = {}
        n_media_count = {}
        for n in news:
            n_time[n.id] = make_readble_time(n.creation_date)
            if n.media:
                n_media[n.id] = n.media.split(", ")
                n_media_type[n.id] = n.media_type.split(", ")
                n_media_count[n.id] = len(n.media.split(", "))
        return render_template("news.html", current_user=current_user, news=news, n_time=n_time, n_media=n_media,
                               n_media_type=n_media_type, n_media_count=n_media_count, media_pics=POST_MEDIA_PIC_TYPES,
                               media_vid=POST_MEDIA_VID_TYPES, media_aud=POST_MEDIA_AUD_TYPES,
                               max_size=app.config['MAX_CONTENT_LENGTH'] // 1024 // 1024, max_count=MAX_MEDIA_COUNT)
    elif request.method == "POST":
        if (current_user.is_admin or current_user.is_news_publisher) and not current_user.is_banned and \
                current_user.is_authenticated and "post_button" in request.form:
            n = News()
            new_id = db_sess.query(News).count() + 1
            files = request.files.getlist("files[]")
            too_many_files = False
            if files:
                media = []
                media_type = []
                f_count = 0
                for file in files:
                    if allowed_type(file.filename, POST_MEDIA_TYPES) and f_count < MAX_MEDIA_COUNT:
                        filename = "news" + str(new_id) + "_" + str(f_count) + "." + \
                                   file.filename.rsplit('.', 1)[1].lower()
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        media.append(filename)
                        media_type.append(filename.rsplit('.', 1)[1].lower())
                        f_count += 1
                    elif f_count >= MAX_MEDIA_COUNT:
                        too_many_files = True
                        break
                if media:
                    n.media = ", ".join(media)
                if media_type:
                    n.media_type = ", ".join(media_type)
            n.poster_id = current_user.id
            n.topic = request.form["topic"]
            n.text = request.form["text"]
            db_sess.add(n)
            db_sess.commit()
            if too_many_files:
                flash("Новость отправлена, но был превышен лимит файлов на одну новость, поэтому"
                      " часть из них была отброшена", "warning")
            else:
                flash("Новость успешно отправлена", "success")
        elif (current_user.is_admin or current_user.is_news_publisher) and not current_user.is_banned and \
                current_user.is_authenticated and "delete_n_button" in request.form:
            n = db_sess.query(News).filter(News.id == request.form["delete_n_button"]).first()
            if n.media:
                files_to_delete = n.media.split(", ")
                for f in files_to_delete:
                    if os.path.isfile("static/media/from_users/" + f):
                        os.remove("static/media/from_users/" + f)
            db_sess.delete(n)
            db_sess.commit()
            flash("Новость успешно удалена", "success")
        else:
            flash("Нехорошо рыться в HTML для деструктивных действий", "danger")
        return redirect("/news")


@app.route("/public/<public_id>", methods=["POST", "GET"])
def public_page(public_id):
    update_user_auth_time()
    db_sess = db_session.create_session()
    public = db_sess.query(Public).filter(Public.id == public_id).first()
    if public:
        if not request.args.get("page"):
            return redirect("/public/" + public_id + "?page=1")
        else:
            try:
                page = int(request.args["page"])
                if page < 1:
                    return redirect("/public/" + public_id + "?page=1")
            except ValueError:
                return redirect("/public/" + public_id + "?page=1")
        public_creation_time = make_readble_time(public.creation_date)
        public_admins = public.admins.split(", ")
        if "" in public_admins:
            public_admins.remove("")
        if current_user.is_authenticated:
            if str(current_user.id) in public_admins:
                admin_tools = True
            else:
                admin_tools = False
        else:
            admin_tools = False
        public_moderators = public.moderators.split(", ")
        if "" in public_moderators:
            public_moderators.remove("")
        if current_user.is_authenticated:
            if str(current_user.id) in public_moderators:
                moderator_tools = True
            else:
                moderator_tools = False
        else:
            moderator_tools = False
        subscribers = public.who_subscribed.split(", ")
        if "" in subscribers:
            subscribers.remove("")
        if current_user.is_authenticated:
            if str(current_user.id) in subscribers:
                is_subscriber = True
            else:
                is_subscriber = False
        else:
            is_subscriber = False
        posts = db_sess.query(Post).filter(public.id == Post.public_id, Post.parent_post == None)
        posts_c = posts.count()
        if posts_c:
            max_page_of_public = posts_c // POSTS_IN_PAGE_MAX
            if posts_c % POSTS_IN_PAGE_MAX:
                max_page_of_public += 1
        else:
            max_page_of_public = 1
        if page > max_page_of_public and page != 1:
            return redirect("/public/" + public + "?page=" + str(max_page_of_public))
        if request.method == "GET":
            last_n = db_sess.query(News).get(db_sess.query(News).count())
            if last_n:
                last_n_time = make_readble_time(last_n.creation_date)
            else:
                last_n_time = None
            post_time = {}
            post_media = {}
            post_media_type = {}
            post_media_count = {}
            post_likers = {}
            for post in posts:
                post_time[post.id] = make_readble_time(post.creation_date)
                if post.media:
                    post_media[post.id] = post.media.split(", ")
                    post_media_type[post.id] = post.media_type.split(", ")
                    post_media_count[post.id] = len(post.media.split(", "))
                post_likers[post.id] = post.who_liked.split(", ")
                if "" in post_likers[post.id]:
                    post_likers[post.id].remove("")
            comments = {}
            comments_posters = {}
            comments_time = {}
            comments_likers = {}
            for p in posts:
                comments[p.id] = db_sess.query(Post).filter(Post.parent_post == p.id)
                for comm in comments[p.id]:
                    comments_posters[comm.id] = db_sess.query(User).filter(comm.poster_id == User.id).first()
                    comments_time[comm.id] = make_readble_time(comm.creation_date)
                    comments_likers[comm.id] = comm.who_liked.split(", ")
                    if "" in comments_likers[comm.id]:
                        comments_likers[comm.id].remove("")
            return render_template("public.html", current_user=current_user, last_n=last_n, last_n_time=last_n_time,
                                   last_n_text=make_text_news(last_n.text) if last_n else None, public=public,
                                   admin_tools=admin_tools, page=page, max_page_of_public=max_page_of_public,
                                   posts=posts, posts_c=posts_c, media_pics=POST_MEDIA_PIC_TYPES,
                                   post_likers=post_likers, media_vid=POST_MEDIA_VID_TYPES,
                                   media_aud=POST_MEDIA_AUD_TYPES, accept_files=accept_post_media,
                                   post_time=post_time, max_size=app.config['MAX_CONTENT_LENGTH'] // 1024 // 1024,
                                   max_count=MAX_MEDIA_COUNT, post_media=post_media, post_media_type=post_media_type,
                                   post_media_count=post_media_count, comments=comments, page_max=POSTS_IN_PAGE_MAX,
                                   comments_posters=comments_posters, comments_time=comments_time,
                                   comments_likers=comments_likers, is_subscriber=is_subscriber,
                                   moderator_tools=moderator_tools, public_creation_time=public_creation_time)
        elif request.method == "POST":
            if "to_the_beginning_button" in request.form:
                return redirect("/public/" + public_id + "?page=" + str(request.form["to_the_beginning_button"]))
            elif "to_the_end_button" in request.form:
                return redirect("/public/" + public_id + "?page=" + str(request.form["to_the_end_button"]))
            elif "to_the_previous_button" in request.form:
                return redirect("/public/" + public_id + "?page=" + str(request.form["to_the_previous_button"]))
            elif "to_the_next_button" in request.form:
                return redirect("/public/" + public_id + "?page=" + str(request.form["to_the_next_button"]))
            if current_user.is_authenticated:
                if "like_button" in request.form:
                    post = db_sess.query(Post).filter(Post.id == request.form["like_button"]).first()
                    if post:
                        who_liked = post.who_liked.split(", ")
                        if "" in who_liked:
                            who_liked.remove("")
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
                    return redirect("/public/" + public_id + "?page=" + str(page))
                elif "subscribe_button" in request.form:
                    who_subscribed = public.who_subscribed.split(", ")
                    if "" in who_subscribed:
                        who_subscribed.remove("")
                    if str(current_user.id) in who_subscribed:
                        who_subscribed.remove(str(current_user.id))
                        public.subscribers -= 1
                        msg = "Подписка отменена"
                    else:
                        who_subscribed.append(str(current_user.id))
                        public.subscribers += 1
                        msg = "Ты подписался"
                    public.who_subscribed = ", ".join(who_subscribed)
                    db_sess.commit()
                    flash(msg, "success")
                if admin_tools or moderator_tools:
                    if "about_button" in request.form and not current_user.is_banned and not public.is_banned:
                        public.about = request.form["about_input"]
                        db_sess.commit()
                        flash("Описание успешно обновлено", "success")
                    elif "post_button" in request.form and not current_user.is_banned and not public.is_banned:
                        post = Post()
                        files = request.files.getlist("files[]")
                        too_many_files = False
                        if files:
                            media = []
                            media_type = []
                            f_count = 0
                            for file in files:
                                if allowed_type(file.filename, POST_MEDIA_TYPES) and f_count < MAX_MEDIA_COUNT:
                                    filename = str(time()).replace(".", "_") + "_" + str(f_count) + "." + \
                                               file.filename.rsplit('.', 1)[1].lower()
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
                        post.public_id = public.id
                        post.text = request.form["text"]
                        db_sess.add(post)
                        db_sess.commit()
                        if too_many_files:
                            flash("Пост отправлен, но был превышен лимит файлов на один пост, поэтому"
                                  " часть из них была отброшена", "warning")
                        else:
                            flash("Пост успешно отправлен", "success")
                        return redirect("/public/" + public_id + "?page=1")
                    elif "comment_button" in request.form and not current_user.is_banned:
                        if request.form.get("comment_text").replace(" ", ""):
                            comment = Post()
                            comment.poster_id = current_user.id
                            comment.parent_post = request.form["comment_button"]
                            comment.text = request.form["comment_text"]
                            db_sess.add(comment)
                            db_sess.commit()
                            flash("Комментарий успешно отправлен", "success")
                        else:
                            flash("Сначала нужно что-нибудь написать", "danger")
                    elif "delete_post_button" in request.form and not current_user.is_banned and not public.is_banned:
                        post = db_sess.query(Post).filter(Post.id == request.form["delete_post_button"]).first()
                        if post.media:
                            files_to_delete = post.media.split(", ")
                            for f in files_to_delete:
                                if os.path.isfile("static/media/from_users/" + f):
                                    os.remove("static/media/from_users/" + f)
                        db_sess.delete(post)
                        db_sess.commit()
                        flash("Пост успешно удалён", "success")
                    elif current_user.is_banned:
                        flash("Ты был забанен, поэтому отправлять с этого аккаунта больше ничего нельзя, "
                              "только смотреть. Причина бана: " + current_user.ban_reason, "danger")
                    elif public.is_banned:
                        flash("Это сообщество было забанено, поэтому отправлять с него больше ничего нельзя. "
                              "Причина бана: " + current_user.ban_reason, "danger")
                else:
                    if "ban_public_button" in request.form and current_user.is_admin and not public.is_banned:
                        if request.form.get("reason_text"):
                            public.ban_reason = request.form["reason_text"]
                            public.is_banned = True
                            db_sess.commit()
                            flash("Пользователь успешно забанен", "success")
                        else:
                            flash("Необходимо указать причину бана", "danger")
                    elif "unban_public_button" in request.form and current_user.is_admin and public.is_banned:
                        public.ban_reason = None
                        public.is_banned = False
                        db_sess.commit()
                        flash("Пользователь успешно разбанен", "success")
                    elif "delete_post_button" in request.form and not current_user.is_banned:
                        post = db_sess.query(Post).filter(Post.id == request.form["delete_post_button"]).first()
                        if post.poster_id == current_user.id or current_user.is_admin:
                            if post.media:
                                files_to_delete = post.media.split(", ")
                                for f in files_to_delete:
                                    if os.path.isfile("static/media/from_users/" + f):
                                        os.remove("static/media/from_users/" + f)
                            db_sess.delete(post)
                            db_sess.commit()
                            flash("Пост успешно удалён", "success")
                        else:
                            flash("Нельзя удалить этот пост", "danger")
                    elif "comment_button" in request.form and not current_user.is_banned and not public.is_banned:
                        if request.form.get("comment_text").replace(" ", ""):
                            comment = Post()
                            comment.poster_id = current_user.id
                            comment.parent_post = request.form["comment_button"]
                            comment.text = request.form["comment_text"]
                            db_sess.add(comment)
                            db_sess.commit()
                            flash("Комментарий успешно отправлен", "success")
                        else:
                            flash("Сначала нужно что-нибудь написать", "danger")
            return redirect("/public/" + public_id)
    else:
        abort(404)


@app.route("/public/<public_id>/settings", methods=["POST", "GET"])
@login_required
def public_settings(public_id):
    update_user_auth_time()
    db_sess = db_session.create_session()
    public = db_sess.query(Public).filter(Public.id == public_id).first()
    if public:
        public_admins = public.admins.split(", ")
        if "" in public_admins:
            public_admins.remove("")
        if not str(current_user.id) in public_admins:
            abort(403)
        if request.method == "GET":
            if current_user.is_banned:
                flash("Тебе нельзя настраивать сообщество, так как ты забанен", "danger")
                return redirect("/public/" + public_id)
            elif public.is_banned:
                flash("Нельзя настраивать забаненное сообщество", "danger")
                return redirect("/public/" + public_id)
            return render_template("public_settings.html", current_user=current_user, accept_avatars=accept_avatars,
                                   public=public)
        elif request.method == "POST":
            if not current_user.is_banned and not public.is_banned:
                all_is_ok = True
                error_message = "Настройки обновлены частично, случились проблемы с:"
                if "clear_button" in request.form and public.avatar:
                    if os.path.isfile("static/media/from_users/avatars/" + public.avatar):
                        os.remove("static/media/from_users/avatars/" + public.avatar)
                    public.avatar = None
                    db_sess.commit()
                elif "set_button" in request.form:
                    if name_is_correct(request.form.get("name")):
                        public.name = request.form["name"]
                    elif request.form.get("name") != "" and request.form.get("name") != None:
                        error_message += "\nНазванием"
                        all_is_ok = False
                    file = request.files["file"]
                    if file and allowed_type(file.filename, AVATAR_TYPES):
                        if public.avatar != None:
                            if os.path.isfile("static/media/from_users/avatars/" + public.avatar):
                                os.remove("static/media/from_users/avatars/" + public.avatar)
                        filename = "public_avatar" + str(public.id) + "." + file.filename.rsplit('.', 1)[1].lower()
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/avatars", filename))
                        public.avatar = filename
                    elif file and not allowed_type(file.filename, AVATAR_TYPES):
                        error_message += "\nАватаркой"
                        all_is_ok = False
                    db_sess.commit()
                if all_is_ok:
                    flash("Настройки обновлены", "success")
                else:
                    flash(error_message, "warning")
            else:
                flash("Нельзя настраивать забаненный аккаунт", "danger")
            return redirect("/public/" + public_id)
    else:
        abort(404)


@app.route("/public", methods=["POST", "GET"])
def public_list_page():
    update_user_auth_time()
    db_sess = db_session.create_session()
    if request.method == "GET":
        publics = db_sess.query(Public)
        if current_user.is_authenticated:
            publics_subscribed = []
            publics_admin_or_mod = []
            for public in publics:
                subscrbers = public.who_subscribed.split(", ")
                admin = public.admins.split(", ")
                mod = public.moderators.split(", ")
                if str(current_user.id) in subscrbers:
                    publics_subscribed.append(public)
                if str(current_user.id) in admin or str(current_user.id) in mod:
                    publics_admin_or_mod.append(public)
        last_n = db_sess.query(News).get(db_sess.query(News).count())
        if last_n:
            last_n_time = make_readble_time(last_n.creation_date)
        else:
            last_n_time = None
        return render_template("public_list.html", current_user=current_user, last_n=last_n, last_n_time=last_n_time,
                               last_n_text=make_text_news(last_n.text) if last_n else None, publics=publics,
                               publics_c=publics.count(),
                               publics_subscribed=publics_subscribed if current_user.is_authenticated else None,
                               publics_subscribed_c=len(publics_subscribed) if current_user.is_authenticated else None,
                               publics_admin_or_mod=publics_admin_or_mod if current_user.is_authenticated else None,
                               publics_admin_or_mod_c=len(publics_admin_or_mod)
                               if current_user.is_authenticated else None)
    elif request.method == "POST":
        if "create_public_button" in request.form and request.form.get("name") and not current_user.is_banned:
            public_id = db_sess.query(Public).count() + 1
            public = Public()
            public.admins = str(current_user.id)
            public.name = request.form["name"]
            public.about = request.form["about"] if request.form.get("about") else ""
            db_sess.add(public)
            db_sess.commit()
            flash("Сообщество создано", "success")
            return redirect("/public/" + str(public_id))
        return redirect("/public")


@app.route("/messages", methods=["POST", "GET"])
@login_required
def messages_page():
    update_user_auth_time()
    db_sess = db_session.create_session()
    if request.method == "GET":
        users = db_sess.query(User).filter(User.id != current_user.id)
        text_to_search = request.args.get("req")
        needed_users = []
        if text_to_search:
            text_to_search = [x.lower() for x in text_to_search.split("+")]
            for user in users:
                for t in text_to_search:
                    if user.patronymic:
                        if t in user.name.lower() or t in user.surname.lower() or t in user.login.lower() or \
                                t in user.patronymic.lower():
                            needed_users.append(user)
                    else:
                        if t in user.name.lower() or t in user.surname.lower() or t in user.login.lower():
                            needed_users.append(user)
            users_c = len(needed_users)
        else:
            users_c = users.count()
        return render_template("messages_list.html", current_user=current_user, users=users,
                               text_to_search=text_to_search, users_c=users_c)
    elif request.method == "POST":
        pass

@app.route("/messages/<user_id>", methods=["POST", "GET"])
@login_required
def messages_with_user(user_id):
    update_user_auth_time()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(user_id == User.id).first()
    if user:
        if user.id == current_user.id:
            flash("Нельзя писать самому себе", "danger")
            return redirect("/messages")
        else:
            if request.method == "GET":
                return render_template("messages.html", user=user, current_user=current_user)
            elif request.method == "POST":
                pass
    else:
        flash("Такого пользователя не существует", "danger")
        return redirect("/messages")

@app.route("/logout")
@login_required
def logout():
    update_user_auth_time()
    logout_user()
    if request.args.get("from"):
        return redirect(request.args.get("from"))
    return redirect("/")


@app.route("/random")
def go_to_random_user():
    update_user_auth_time()
    db_sess = db_session.create_session()
    users = db_sess.query(User)
    if users.count():
        user = random.choice(list(users))
        return redirect("/user/" + user.login)
    else:
        flash("На данный момент никто не зарегистрирован", "danger")
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
    flash("[Ошибка 403] Cмотреть данную страницу/делать данное действие можно только администраторам", "warning")
    return redirect("/login")


@app.errorhandler(404)
def e404(code):
    update_user_auth_time()
    print(code)
    return render_template("error.html", current_user=current_user, link=request.args.get("from"),
                           code=404, err="Мы не можем показать тебе эту страницу: её не существует",
                           pics=PICS_404)


@app.errorhandler(500)
def e500(code):
    update_user_auth_time()
    print(code)
    return render_template("error.html", current_user=current_user, code=500,
                           err="Извини за неудобство, но сайт по какой-то причине подписал отказ в "
                           "показе страницы. Сейчас мы активно работаем над причиной проблемы и"
                           " исправляем её", pics=PICS_500)


if not PYTHONANYWHERE:
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
else:
    db_session.global_init("db/social_network.db")