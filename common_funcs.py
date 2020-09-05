from database import get_db
from flask import session, redirect, url_for
from functools import wraps


def current_user_record():
    user_result = None
    if user := session.get('user', None):
        db = get_db()
        user_cur = db.execute('select id, name, password, expert, admin from users where name = ?', [user])
        user_result = user_cur.fetchone()
    return user_result


def restricted(role):
    def is_user(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = current_user_record()
            if not user:
                return redirect(url_for('login'))
            elif not user[role]:
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return is_user


def is_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user_record():
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper
