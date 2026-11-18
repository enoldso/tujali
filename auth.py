from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from forms import LoginForm
from models import db, now, User

bp = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to continue.'
login_manager.session_protection = 'strong'

HOME_BY_ROLE = {'admin': 'admin.dashboard', 'specialist': 'portal.dashboard',
                'health_officer': 'health.dashboard'}


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def roles_required(*roles):
    """Allow only these roles (admins are always allowed)."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != 'admin' and current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def home_url(user):
    return url_for(HOME_BY_ROLE.get(user.role, 'public.index'))


def _safe_next(target):
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith('/'):
        return None
    return target


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(home_url(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.is_active and user.check_password(form.password.data):
            session.clear()
            login_user(user, remember=form.remember.data)
            user.last_login_at = now()
            db.session.commit()
            return redirect(_safe_next(request.args.get('next')) or home_url(user))
        flash('Incorrect email or password.', 'danger')
    return render_template('login.html', form=form)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('public.index'))


@bp.route('/home')
@login_required
def home():
    return redirect(home_url(current_user))
