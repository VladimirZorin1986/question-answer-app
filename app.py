from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from common_funcs import current_user_record, is_login, restricted

app = Flask('__name__')
app.config.from_object(Config)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3_db'):
        g.sqlite3_db.close()


@app.route('/')
def index():
    user = current_user_record()
    db = get_db()
    questions_cur = db.execute('select questions.id as question_id, questions.question_text, '
                               'askers.name as asker_name, experts.name as expert_name from questions '
                               'join users as askers on askers.id = questions.asked_by_id '
                               'join users as experts on experts.id = questions.expert_id '
                               'where answer_text is not null')
    questions = questions_cur.fetchall()

    return render_template('home.html', user=user, questions=questions)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = current_user_record()
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']

        existing_user_cur = db.execute('select id from users where name = ?', [name])
        existing_user = existing_user_cur.fetchone()
        if existing_user:
            return render_template('register.html', user=user, error='User is already exist!')

        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)',
                   [name, hashed_password, '0', '0'])
        db.commit()
        session['user'] = request.form['name']
        return redirect(url_for('index'))
    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = current_user_record()
    error = None
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        db = get_db()
        user_cur = db.execute('select id, name, password from users where name = ?', [name])
        user_result = user_cur.fetchone()

        if user_result:
            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                error = 'Password is incorrect!'
        else:
            error = 'Username is incorrect!'

    return render_template('login.html', user=user, error=error)


@app.route('/question/<question_id>')
def question(question_id):
    user = current_user_record()
    db = get_db()
    question_cur = db.execute('select questions.question_text, questions.answer_text, '
                              'askers.name as asker_name, experts.name as expert_name '
                              'from questions join users as askers on askers.id = questions.asked_by_id '
                              'join users as experts on experts.id = questions.expert_id '
                              'where questions.id = ?', [question_id])
    question_result = question_cur.fetchone()
    return render_template('question.html', user=user, question_result=question_result)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
@restricted('expert')
def answer(question_id):
    user = current_user_record()
    db = get_db()
    if request.method == 'POST':
        current_answer = request.form['answer']
        db.execute('update questions set answer_text = ? where id = ?', [current_answer, question_id])
        db.commit()
        return redirect(url_for('unanswered'))
    question_cur = db.execute('select id, question_text from questions where id = ?', [question_id])
    current_question = question_cur.fetchone()
    return render_template('answer.html', user=user, current_question=current_question)


@app.route('/ask', methods=['GET', 'POST'])
@is_login
def ask():
    user = current_user_record()
    db = get_db()
    if request.method == 'POST':
        new_question = request.form['question']
        expert_id = request.form['expert']
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?)',
                   [new_question, user['id'], expert_id])
        db.commit()
        return redirect(url_for('index'))
    expert_cur = db.execute('select id, name from users where expert = 1')
    experts = expert_cur.fetchall()
    return render_template('ask.html', user=user, experts=experts)


@app.route('/unanswered')
@restricted('expert')
def unanswered():
    user = current_user_record()
    db = get_db()
    question_cur = db.execute('select questions.id, questions.question_text, users.name from questions '
                              'join users on users.id = questions.asked_by_id '
                              'where questions.answer_text is null and questions.expert_id = ?', [user['id']])
    questions = question_cur.fetchall()
    return render_template('unanswered.html', user=user, questions=questions)


@app.route('/users')
@restricted('admin')
def users():
    user = current_user_record()
    db = get_db()
    user_cur = db.execute('select id, name, admin, expert from users')
    user_results = user_cur.fetchall()
    return render_template('users.html', user=user, user_results=user_results)


@app.route('/promote/<user_id>')
@restricted('admin')
def promote(user_id):
    db = get_db()
    db.execute('update users set expert = 1 where id = ?', [user_id])
    db.commit()
    return redirect(url_for('users'))


@app.route('/logout')
@is_login
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))
