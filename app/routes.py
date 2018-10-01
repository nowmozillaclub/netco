from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from flask_login import current_user, login_user
from app.models import User
from flask_login import logout_user
from flask_login import login_required
from flask import request
from werkzeug.urls import url_parse
from app import db
from app.forms import RegistrationForm
from datetime import datetime
from app.forms import EditProfileForm
from app.forms import PostEventForm
from app.forms import ManageForm
from app.models import Post
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm
from flask import g
from flask_babel import _, get_locale
from guess_language import guess_language

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.locale = str(get_locale())

@app.route('/', methods=['GET', 'POST'])
def first():
    return render_template('home.html', title=_('Home'))

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.type == 'student':
        return redirect(url_for('home'))
    form = PostEventForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5 :
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language, event=form.event.data, link=form.link.data, type=form.type.data)
        db.session.add(post)
        db.session.commit()
        flash(_('Your Event has been added.'))
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                            posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

@app.route('/applications', methods=['GET', 'POST'])
@login_required
def applications():
    if current_user.type == 'student':
        return redirect(url_for('home'))
    users=User.query.all()
    return render_template('applications.html', title=_('Applications'), users=users)

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if current_user.type == 'committee':
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'),
                            posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.type == 'committee':
                next_page = url_for('index')
            else:
                next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect (url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, type=form.type.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations! User successfully created!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
           page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username = user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username = user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.type == 'student':
        return redirect(url_for('manage'))
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.name = form.name.data
        current_user.departments = form.departments.data
        db.session.commit()
        flash (_('Your changes have been saved.'))
        return redirect(url_for('manage'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.name.data = current_user.name
        form.departments.data = current_user.departments

    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)

@app.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    if current_user.type == 'committee':
        return redirect(url_for('edit_profile'))
    form = ManageForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.departments = form.departments.data
        current_user.about_me = form.about_me.data
        current_user.experience = form.experience.data
        current_user.why = form.why.data
        db.session.commit()
        flash (_('Your changes have been saved.'))
        return redirect(url_for('manage'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.phone_number.data = current_user.phone_number
        form.departments.data = current_user.departments
        form.about_me.data = current_user.about_me
        form.experience.data = current_user.experience
        form.why.data = current_user.why
    return render_template('manage.html', title=_('Manage'), form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("Couldn't find user: %(username)s",username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_("Um... You can't really follow yourself ya' know..."))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are now following %(username)s!', username=username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Could not find %(username)s'.format(username)))
        return redirect(url_for('index'))
    if user == current_user:
        flash (_("You can't really unfollow yourself man..."))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('Successfully unfollowed %(username)s.', username=username))
    return redirect(url_for('user', username=username))

@app.route('/apply/<username>')
@login_required
def apply(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("Couldn't find committee: %(username)s",username=username))
        return redirect(url_for('index'))
    current_user.apply(user)
    db.session.commit()
    flash(_('Successfully Applied for %(username)s!', username=username))
    return redirect(url_for('user', username=username))

@app.route('/unapply/<username>')
@login_required
def unapply(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Could not find %(username)s'.format(username)))
        return redirect(url_for('index'))
    current_user.unapply(user)
    db.session.commit()
    flash(_('Successfully rescinded application for %(username)s.', username=username))
    return redirect(url_for('user', username=username))

@app.route('/deleteApplication/<username>')
@login_required
def deleteApplication(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Could not find %(username)s'.format(username)))
        return redirect(url_for('index'))
    user.unapply(current_user)
    db.session.commit()
    flash(_('Successfully deleted application for %(username)s.', username=username))
    return redirect(url_for('applications'))

@app.route('/explore')
# @login_required
def explore():
    page = request.args.get('page', 1 , type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                            posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash (_('Check your email for instructions!'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title=_('Reset Password'), form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user=User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        dn.session.commit()
        flash(_('Password has been successfully reset!'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/clearall')
@login_required
def clearall():
    posts = Post.query.all()
    for p in posts:
        if p.author == current_user:
            db.session.delete(p)
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<current_post>')
@login_required
def delete(current_post):
    posts = Post.query.all()
    for p in posts:
        if p.author == current_user:
            if str(p) == current_post:
                db.session.delete(p)
                db.session.commit()
    return redirect(url_for('index'))
