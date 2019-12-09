import psycopg2
from flask import Flask, render_template, request, jsonify, session, redirect
import constant
from werkzeug.security import generate_password_hash,  check_password_hash

app = Flask(__name__)


conn = psycopg2.connect(host=constant.host, dbname=constant.dbname, user=constant.username, password=constant.password)
cur = conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')

#
# @app.route('/db')
# def db():
#     cur.execute("select * from languages where name=%s", ('Python',))
#     metros_info = cur.fetchall()
#     json_response = {
#         'language': []
#     }
#     print(metros_info)
#     for i in metros_info:
#
#         json_response['language'].append(i)
#     return jsonify(json_response)


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        print(password)
        phone = request.form['phone']
        if len(request.form) == 6:
            name_table = 'programmer'

            cur.execute('select email from customer where email=%s',(email,))
            if cur.fetchall() != []:
                return 'Вы являетесь работодателем и не можете зарегистрироваться, как программист'
        else:
            name_table = 'customer'
            cur.execute('select email from programmer where email=%s', (email,))
            if cur.fetchall() != []:
                return 'Вы являетесь программистом и не можете зарегистрироваться, как разработчик'

        try:
            cur.execute(
                f'insert into {name_table} (email, password, first_name, last_name, phone, stars) values (%s, %s,%s,%s,%s, %s)',
                (email, password, first_name, last_name, phone, 0))
            conn.commit()
            session['email'] = email
            session['type'] = name_table
        except psycopg2.errors.UniqueViolation:
            conn.commit()
            return render_template('error_registr.html')

    return redirect('/test')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur.execute('select email,password from programmer where email = (%s)', (email,))
        programmer = cur.fetchall()
        cur.execute('select email,password from customer where email = (%s)', (email,))
        customer = cur.fetchall()
        if programmer == [] and customer == []:
            return render_template('error_login.html')
        elif customer == []:
            if not (check_password_hash(programmer[0][1], password)):
                return render_template('error_login.html')
            session['email'] = email
            session['type'] = 'programmer'
        else:
            if not (check_password_hash(customer[0][1], password)):
                return render_template('error_login.html')
            session['email'] = email
            session['type'] = 'customer'
        conn.commit()
    return redirect('/profile')

@app.route('/logout')
def logout():
       # remove the username from the session if it is there
       session.pop('email', None)
       return render_template('index.html')



@app.route('/test')
def test():
    print(session['type'])
    if session['type'] == 'programmer':
        cur.execute('select description from programmer where email=%s',(session['email'],))
        if cur.fetchone()[0] is None:
            return redirect('/description')
        conn.commit()
    return render_template('profile.html')


@app.route('/description')
def description():
    cur.execute('select * from languages')
    languages = cur.fetchall()
    cur.execute('select * from areas')
    areas = cur.fetchall()
    conn.commit()
    all_lang = []
    all_areas = []

    for lang in languages:
        lang_info = {
            'id': lang[1],
            'name': lang[0],
        }
        all_lang.append(lang_info)

    for area in areas:
        area_info = {
            'name': area[1],
            'id': area[0],
        }
        all_areas.append(area_info)

    return render_template('prog_information.html', languages=all_lang, areas=all_areas)



@app.route('/interests', methods=['POST'])
def interests():
    languages = request.form.getlist('lang')
    areas = request.form.getlist('area')
    description = request.form['description']
    email = session['email']

    for i in areas:
        cur.execute('select * from areas where id=%s', (i,))
        area = cur.fetchone()
        if area != []:
            cur.execute('select * from programmer_areas where areas_id=%s and programmer_email=%s', (i,email,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into programmer_areas (programmer_email, areas_id) values (%s, %s)',
                    (email, i))

    for i in languages:
        cur.execute('select * from languages where id=%s', (i,))
        lang = cur.fetchone()
        if lang != []:
            cur.execute('select * from programmer_languages where languages_id=%s and programmer_email=%s', (i, email,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into programmer_languages (programmer_email, languages_id) values (%s, %s)',
                    (email, i))

    cur.execute(
        'update programmer set description=%s where email=%s',
        (description,email))

    conn.commit()
    return redirect('/profile')

@app.route('/profile')
def profile():
    email = session['email']
    if session['type'] == 'programmer':
        sql1 = """
        SELECT name FROM areas
        WHERE id IN
            (SELECT areas_id 
             FROM programmer_areas
             WHERE programmer_email=%s)"""
        sql2 = """
                SELECT name FROM languages
                WHERE id IN
                    (SELECT languages_id 
                    FROM programmer_languages
                    WHERE programmer_email=%s)"""
        sql3 = """
        SELECT first_name, last_name, description FROM programmer WHERE email=%s"""
        cur.execute(sql1, (email,))
        areas = cur.fetchall()
        cur.execute(sql2, (email,))
        langs = cur.fetchall()
        cur.execute(sql3, (email,))
        person = cur.fetchone()
        conn.commit()

        all_lang = []
        all_areas = []

        for i in areas:
            all_areas.append(i[0])
        for i in langs:
            all_lang.append(i[0])
        name = person[0] + " " + person[1]
        description = person[2]

        session['languages'] = all_lang
        session['areas'] = all_areas

        return render_template('profile.html', languages=all_lang, areas=all_areas, name=name, description=description, status=session['type'])
    else:
        sql4 = """
                SELECT first_name, last_name FROM customer WHERE email=%s"""
        cur.execute(sql4, (email,))
        person = cur.fetchone()
        conn.commit()
        name = person[0] + " " + person[1]
        return render_template('profile.html', name=name, status=session['type'])


@app.route('/create_orders', methods=['GET'])
def orders():
    cur.execute('select * from languages')
    languages = cur.fetchall()
    cur.execute('select * from areas')
    areas = cur.fetchall()
    conn.commit()
    all_lang = []
    all_areas = []

    for lang in languages:
        lang_info = {
            'id': lang[1],
            'name': lang[0],
        }
        all_lang.append(lang_info)

    for area in areas:
        area_info = {
            'name': area[1],
            'id': area[0],
        }
        all_areas.append(area_info)

    return render_template('create_orders.html', languages=all_lang, areas=all_areas)

@app.route('/add_orders', methods=['POST'])
def add_orders():
    email = session['email']
    languages = request.form.getlist('lang')
    areas = request.form.getlist('area')
    description = request.form['description']

    cur.execute('insert into orders (description, customer_email) values (%s, %s) returning id ', (description, email))
    order_id = cur.fetchone()[0]

    for i in areas:
        cur.execute('select * from areas where id=%s', (i,))
        area = cur.fetchone()
        if area != []:
            cur.execute('select * from orders_areas where areas_id=%s and orders_id=%s', (i, order_id,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into orders_areas (orders_id, areas_id) values (%s, %s)',
                    (order_id, i))


    for i in languages:
        cur.execute('select * from languages where id=%s', (i,))
        lang = cur.fetchone()
        if lang != []:
            cur.execute('select * from orders_languages where languages_id=%s and orders_id=%s', (i, order_id,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into orders_languages (orders_id, languages_id) values (%s, %s)',
                    (order_id, i))
    conn.commit()
    return redirect('/profile')

@app.route('/find_order', methods=['GET'])
def find_order():
    type = session['type']
    if type == 'programmer':
        all_lang = session['languages']
        all_areas = session['areas']

        orders_id = []
        for i in all_lang:
            sql = """
            SELECT orders_id FROM orders_languages
            WHERE languages_id IN
            (SELECT id 
             FROM languages
             WHERE name=%s)"""
            cur.execute(sql, (i,))
            ord = cur.fetchall()
            conn.commit()
            for j in ord:
                orders_id.append(j)

        for i in all_areas:
            sql = """
            SELECT orders_id FROM orders_areas
            WHERE areas_id IN
            (SELECT id 
             FROM areas
             WHERE name=%s)"""
            cur.execute(sql, (i,))
            ord = cur.fetchall()
            conn.commit()
            for j in ord:
                orders_id.append(j)
        all_orders = []
        for i in orders_id:
            cur.execute('select * from orders where id = %s ', (i,))
            order = cur.fetchone()
            order_info = {
                'id': order[0],
                'description': order[1],
                'customer_name': order[2],
            }
            all_orders.append(order_info)
            conn.commit()

        return render_template("tasks.html", orders=all_orders)
    else:
        return render_template("tasks.html")

@app.route('/order_info/<int:order_id>', methods=['GET'])
def order_info(order_id):
    cur.execute('select * from orders where id = %s', (order_id,))
    order = cur.fetchone()
    conn.commit()
    description = order[1]
    customer_name = order[2]

    sql1 = """
            SELECT name FROM areas
            WHERE id IN
                (SELECT areas_id 
                 FROM orders_areas
                 WHERE orders_id=%s)"""
    sql2 = """
                    SELECT name FROM languages
                    WHERE id IN
                        (SELECT languages_id 
                        FROM orders_languages
                        WHERE orders_id=%s)"""

    cur.execute(sql1, (order_id,))
    languages = cur.fetchall()
    cur.execute(sql2, (order_id,))
    areas = cur.fetchall()
    conn.commit()
    order_info = {
        'id': order_id,
        'description': description,
        'customer_name': customer_name,
        'languages': [i[0] for i in languages],
        'areas': [i[0] for i in areas]
    }

    return render_template('orders.html', orders=order_info, status=session['type'])

# status 1 - программист хочет взять заказ, но не одобрен еще заказчиком
# status 0 - программист хотел взять заказ, но заказчик отказался
# status 2 - программист получил заказ, он в процессе работы
# status 3 - программист выполнил заказ
@app.route('/take_order<int:order_id>', methods=['POST', 'GET'])
def take_order(order_id):
    email = session['email']
    cur.execute('insert into programmers_orders (programmer_email, orders_id, status) values (%s,%s,%s)', (email, order_id, 1))
    conn.commit()
    return redirect('/find_order')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)
